import os
import re
import asyncio
import json
from typing import AsyncGenerator, Dict, List, Tuple
from dotenv import load_dotenv

import httpx

# 读取历史故事
from app.services.storage import get_story_turns


# ====== Config ======
load_dotenv()  # 自动读取 .env

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # 'deepseek' or 'gemini'

# 双模型路由
LLM_MODEL_CHAT = os.getenv("LLM_MODEL_CHAT", "deepseek-chat")
LLM_MODEL_REASONING = os.getenv("LLM_MODEL_REASONING", "deepseek-reasoner")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
MAX_DETECTIVE_ROUNDS = int(os.getenv("MAX_DETECTIVE_ROUNDS", "10"))

# ====== Mock ======
def _mock_turns(user_text: str, rounds: int) -> List[Dict]:
    return [
        {"author": "ai", "text": f"（mock AI）基于：{user_text} 的续写（第{i+1}句）"}
        for i in range(rounds)
    ]

def _mock_suggestions(intent: str, seed: str) -> List[Dict]:
    return [
        {
            "id": "opt_a", 
            "title": "常规展开", 
            "preview": f"顺着[{intent}]的方向继续...", 
            "full_text": f"他看着手中的{seed}，决定{intent}...", 
            "tags": ["#稳妥"]
        },
        {
            "id": "opt_b", 
            "title": "深度结合", 
            "preview": f"{seed}不仅仅是道具...", 
            "full_text": f"原来{seed}背后隐藏着巨大的秘密，这直接导致了{intent}的爆发。", 
            "tags": ["#伏笔", f"#{seed}"]
        },
        {
            "id": "opt_c", 
            "title": "疯狂反转", 
            "preview": "谁也没想到...", 
            "full_text": f"突然，{seed}开始说话了！", 
            "tags": ["#脑洞", "#超展开"]
        }
    ]

# ====== Sentence extraction (robust) ======
_END_PUNCT = r"[。！？.!?]"
_SENT_PATTERN = re.compile(
    rf"""
    (                           # capture 1 complete sentence
      [^\S\r\n]*                # optional leading spaces
      (?:                       # content:
        (?!{_END_PUNCT}+$)      # not only end punct
        [^\r\n]                 # any char except newline
      )+?
      {_END_PUNCT}+             # end punct (one or more)
    )
    """,
    re.VERBOSE,
)

_BAD_ONLY_PUNCT = re.compile(
    r'^[\s"“”‘’\'，,。.！？.!?、:：;；…\-—（）()\[\]【】]+$'
)


def _clean_sentence(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _is_valid_sentence(s: str) -> bool:
    s = _clean_sentence(s)
    if not s:
        return False
    if _BAD_ONLY_PUNCT.match(s):
        return False
    # 至少包含一个“非标点/非空白”的字符
    if not re.search(
        r"[^\s，,。.！？.!?、:：;；…\-—（）()\[\]【】\"“”‘’\']+",
        s,
    ):
        return False
    return True


def extract_complete_sentences(buffer: str) -> Tuple[List[str], str]:
    """
    从 buffer 中抽取所有“已完成句子”（以句末符号结尾），返回 (sentences, remainder)
    remainder 是最后一个未完成的残句
    """
    buffer = buffer or ""
    sentences: List[str] = []
    last_end = 0

    for m in _SENT_PATTERN.finditer(buffer):
        seg = _clean_sentence(m.group(1))
        if _is_valid_sentence(seg):
            sentences.append(seg)
        last_end = m.end()

    remainder = buffer[last_end:] if last_end > 0 else buffer
    remainder = _clean_sentence(remainder)

    return sentences, remainder


# ====== Messages with real context ======
def _build_messages_from_story(story_id: str, user_text: str, continue_hint: str = "") -> List[Dict]:
    """
    ✅ 关键：从 storage 里读取该 story 的历史 turns，按时间顺序拼 messages，
    让模型真正“记得之前写到哪”。
    """
    history = get_story_turns(story_id) or []

    messages: List[Dict] = [
        {
            "role": "system",
            "content": (
                "你是一个擅长互动叙事续写的助手。"
                "请严格延续当前故事的设定、人物与场景继续写，不要新开故事，不要换主角，不要跳出叙事。"
                "输出应是自然的句子，不要只输出标点符号。"
            ),
        }
    ]

    # 控制上下文长度：只取最近 N 条 turns（避免 prompt 太长）
    max_turns = 24
    for t in history[-max_turns:]:
        role = "assistant" if t.get("author") == "ai" else "user"
        text = (t.get("text") or "").strip()
        if text:
            messages.append({"role": role, "content": text})

    # 当前输入放最后
    final_user = (user_text or "").strip() + (continue_hint or "")
    messages.append({"role": "user", "content": final_user})

    return messages


def _auth_headers(api_key: str = None) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key or DEEPSEEK_API_KEY}",
    }


# ====== Non-stream call ======
def _call_deepseek(messages: List[Dict], stream: bool = False, temperature: float = 0.9, model: str = None, config: Dict = {}) -> str:
    if model is None:
        model = config.get("model") or LLM_MODEL_CHAT
    
    base_url = config.get("base_url") or DEEPSEEK_BASE_URL
    api_key = config.get("api_key")
    
    # Remove /v1 suffix if present for clean appending, though standard is usually just base
    # DeepSeek official endpoint is https://api.deepseek.com/chat/completions
    # If user provides https://api.deepseek.com/v1, we handle it carefully or just assume standard
    url = f"{base_url}/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": 8192,
    }
    
    import time
    import random
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(url, headers=_auth_headers(api_key), json=payload)
                resp.raise_for_status()
                data = resp.json()
                print(f"[DeepSeek Raw] Model: {model}, Tokens: {data.get('usage', {})}")
                
                message = data.get("choices", [{}])[0].get("message", {})
                content = message.get("content", "")
                
                if not content and "reasoning_content" in message:
                    print("[DeepSeek] Content is empty, falling back to reasoning_content")
                    return message["reasoning_content"].strip()

                return content.strip()
                
        except Exception as e:
            error_str = str(e)
            # Retry on timeouts, 429, or 5xx server errors
            should_retry = "429" in error_str or "500" in error_str or "502" in error_str or "503" in error_str or "ReadTimeout" in error_str or "ConnectTimeout" in error_str
            
            if should_retry and attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"[DeepSeek Retry] Error encountered, retrying in {delay:.1f}s... (Attempt {attempt+1}/{max_retries}) | Error: {e}")
                time.sleep(delay)
                continue
                
            print(f"[DeepSeek Call Error]: {e}")
            # For user debug visibility
            if api_key or attempt == max_retries:
                return f"[Error] API Call Failed: {str(e)}"
            raise e


def generate_ai_turns(story_id: str, user_text: str, rounds: int, mode: str) -> List[Dict]:
    """
    非流式：自动补齐 rounds。
    ✅ 使用真实上下文（story_id 对应历史 turns），不会开新故事。
    """
    if mode == "human_only":
        return []

    if not DEEPSEEK_API_KEY:
        return _mock_turns(user_text, rounds)

    MAX_CONTINUE_CALLS = 6  # 防止无限继续
    all_sentences: List[str] = []

    try:
        for _ in range(MAX_CONTINUE_CALLS):
            need = rounds - len(all_sentences)
            if need <= 0:
                break

            continue_hint = (
                f"\n\n请在延续上文的前提下继续故事，严格再输出{need}句完整自然的句子，"
                f"每句必须包含内容，不要只输出标点。"
            )

            messages = _build_messages_from_story(story_id, user_text, continue_hint)

            content = _call_deepseek(messages, stream=False, model=LLM_MODEL_CHAT)
            if not content:
                break

            sents, remainder = extract_complete_sentences(content)

            # 一句都切不出来：若整体像句子，则当作一句
            if not sents and _is_valid_sentence(content):
                sents = [_clean_sentence(content)]

            for s in sents:
                if len(all_sentences) >= rounds:
                    break
                all_sentences.append(s)

            # 输出质量太差就停止，避免空转
            if not sents and not remainder:
                break

        if not all_sentences:
            return _mock_turns(user_text, rounds)

        return [{"author": "ai", "text": s} for s in all_sentences[:rounds]]

    except Exception:
        return _mock_turns(user_text, rounds)


def generate_suggestions(context: str, intent: str, seed: str) -> List[Dict]:
    """
    Stateless generation of 3 plot options.
    Uses LLM_MODEL_CHAT for speed.
    """
    if not DEEPSEEK_API_KEY:
        return _mock_suggestions(intent, seed)
    
    sys_prompt = (
        "你是一个小说策划顾问。"
        "请根据提供的[故事上下文]、[意图]和[灵感种子]，构思 3 个截然不同的后续情节发展。"
        "不用写太长，每个选项包含 title (短标题), preview (一句话简介), full_text (段落正文), tags (标签)。"
        "请严格返回 JSON 格式列表。"
    )
    
    user_prompt = f"""
    [Context]: {context[-1000:]}
    [Intent]: {intent}
    [Seed]: {seed}
    
    请生成 JSON:
    [
      {{ "title": "A...", "preview": "...", "full_text": "...", "tags": ["..."] }},
      {{ "title": "B...", "preview": "...", "full_text": "...", "tags": ["..."] }},
      {{ "title": "C...", "preview": "...", "full_text": "...", "tags": ["..."] }}
    ]
    """
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        raw = _call_deepseek(messages, stream=False, temperature=1.0, model=LLM_MODEL_CHAT)
        # Simple JSON extract
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            # Enrich with IDs
            for i, item in enumerate(data):
                item["id"] = f"opt_{i}_{os.urandom(2).hex()}"
            return data
        return _mock_suggestions(intent, seed)
    except Exception as e:
        print(f"Suggestions failed: {e}")
        return _mock_suggestions(intent, seed)


# ====== Stream call helpers ======
async def _call_deepseek_stream(payload: Dict) -> AsyncGenerator[str, None]:
    """
    读取 SSE，yield 增量 delta.content
    """
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, headers=_auth_headers(), json=payload) as resp:
            resp.raise_for_status()

            async for line in resp.aiter_lines():
                if not line:
                    continue

                if line.startswith("data:"):
                    chunk = line[len("data:"):].strip()
                else:
                    chunk = line.strip()

                if chunk == "[DONE]":
                    break

                try:
                    j = httpx.Response(200, content=chunk).json()
                except Exception:
                    continue

                delta = (
                    j.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content", "")
                )
                if delta:
                    yield delta


async def stream_ai_turns(
    story_id: str, user_text: str, rounds: int, mode: str
) -> AsyncGenerator[Dict, None]:
    """
    流式：边到边切句 yield；如果结束后不够 rounds，会自动继续请求补齐。
    ✅ 使用真实上下文（story_id 对应历史 turns），不会开新故事。
    """
    if mode == "human_only":
        return

    if not DEEPSEEK_API_KEY:
        for i in range(rounds):
            await asyncio.sleep(0.35)
            yield {"author": "ai", "text": f"（mock stream）{user_text} -> AI 续写第{i+1}句"}
        return

    MAX_CONTINUE_CALLS = 6
    yielded = 0
    buffer = ""

    try:
        for attempt in range(MAX_CONTINUE_CALLS):
            need = rounds - yielded
            if need <= 0:
                return

            continue_hint = (
                f"\n\n请在延续上文的前提下继续故事，严格再输出{need}句完整自然的句子，"
                f"每句必须包含内容，不要只输出标点。"
            )

            messages = _build_messages_from_story(story_id, user_text, continue_hint)

            payload = {
                "model": LLM_MODEL_CHAT,
                "messages": messages,
                "stream": True,
                "temperature": 0.9,
                "top_p": 0.9,
                "max_tokens": 1024,
            }

            produced_this_attempt = 0

            async for delta in _call_deepseek_stream(payload):
                buffer += delta

                sents, remainder = extract_complete_sentences(buffer)
                buffer = remainder

                for s in sents:
                    if yielded >= rounds:
                        return
                    yielded += 1
                    produced_this_attempt += 1
                    yield {"author": "ai", "text": s}

            # 一次流结束：残句如果像句子，也可以当一句输出
            if yielded < rounds and buffer and _is_valid_sentence(buffer):
                s = _clean_sentence(buffer)
                buffer = ""
                yielded += 1
                produced_this_attempt += 1
                yield {"author": "ai", "text": s}

            # 如果本轮完全没产出，避免死循环
            if attempt > 0 and produced_this_attempt == 0:
                break

    except Exception:
        for i in range(rounds - yielded):
            await asyncio.sleep(0.35)
            yield {
                "author": "ai",
                "text": f"（mock stream fallback）{user_text} -> AI 续写第{yielded + i + 1}句",
            }

def refine_sentence(text: str, context_pre: str, context_post: str, strategy: str) -> str:
    """
    对单句进行润色或升华
    strategy: 'polish' | 'elevate'
    """
    if not text:
        return ""
    
    if not DEEPSEEK_API_KEY:
        # Mock behavior
        if strategy == 'polish':
            return f"(Polished) {text}"
        else:
            return f"(Elevated) {text} 仿佛被注入了新的灵魂。"

    # Build Prompt
    sys_prompt = "你是专业的创意写作助手。"
    
    if strategy == 'polish':
        sys_prompt += "请优化以下句子的流畅度与逻辑连贯性，使其读起来更自然、顺滑，但保留原意。"
    elif strategy == 'elevate':
        sys_prompt += "请升华以下句子，使其更有文学张力、画面感或意外的转折（提高创意熵），可以使用更丰富的辞藻或比喻。"
        
    user_content = f"待修改句子：{text}\n"
    if context_pre:
        user_content += f"前文背景：{context_pre}\n"
    if context_post:
        user_content += f"后文背景：{context_post}\n"
        
    user_content += "\n请直接输出修改后的句子，不要包含任何解释或引号。"

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        return _call_deepseek(messages, stream=False, temperature=0.7 if strategy=='polish' else 1.1, model=LLM_MODEL_CHAT)
    except Exception as e:
        print(f"Refine failed: {e}")
        return text


from google import genai
from google.genai import types

def _call_gemini(messages: List[Dict], temperature: float = 0.9, config: Dict = {}) -> str:
    """
    Call Google Gemini via official SDK (google-genai)
    """
    api_key = config.get("api_key") or GEMINI_API_KEY
    model = config.get("model") or GEMINI_MODEL
    
    if not api_key:
        return "Error: GEMINI_API_KEY not set."

    client = genai.Client(api_key=api_key)
    
    # 1. Extract System Instruction
    sys_instr = None
    processed_msgs = []
    
    for m in messages:
        if m["role"] == "system":
            if sys_instr is None:
                sys_instr = m["content"]
            else:
                sys_instr += "\n\n" + m["content"]
        else:
            role = "user" if m["role"] == "user" else "model"
            processed_msgs.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=m["content"])]
                )
            )

    # 2. Call Generate Content
    import time
    import random
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=processed_msgs,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instr,
                    temperature=temperature,
                    max_output_tokens=8192
                )
            )
            print(f"[Gemini 3.0 Raw Usage] {response.usage_metadata}")
            return response.text.strip()
            
        except Exception as e:
            error_str = str(e)
            is_overloaded = "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str
            
            if is_overloaded and attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"[Gemini Overload] 503/429 encountered, retrying in {delay:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
                continue
                
            print(f"[Gemini SDK Error]: {e}")
            # Pass explicit error back to UI
            if config.get("api_key") or attempt == max_retries:
                 return f"[Gemini Error] {str(e)}"
            raise e


def detective_turn(start: str, end: str, history: List[Dict], config: Dict = {}) -> str:
    """
    海龟汤 - 侦探模式
    Role: 侦探
    Task: 提出封闭式问题/猜想
    History items expect: { "text": "...", "status": "confirmed" | "rejected" | "unknown" }
    """
    # Check config first
    provider = config.get("provider") or LLM_PROVIDER
    
    # Mock fallback if no keys at all (and no custom config)
    if not DEEPSEEK_API_KEY and not GEMINI_API_KEY and not config.get("api_key"):
         # Mock behavior (abbreviated for brevity)
        return "（Mock侦探）这是基于mock的回复，因为没有配置任何API Key。"

    sys_prompt = (
        "你是一名海龟汤侦探。在这个游戏中，我会给你一个故事的【起因】和【结果】。"
        "这两个事件之间存在巨大的逻辑断层，看似毫无关联，甚至自相矛盾。"
        "\n\n"
        "1. 找出连接【起因】和【结果】的隐藏逻辑（中间发生了什么？）。\n"
        "2. 通过提出封闭式问题（是/否）来验证你的猜想。\n"
        "3. 重点关注：为什么起因会导致这个结果？中间缺失了什么关键信息（人物状态、环境隐情、误会等）？"
        "\n\n"
        "规则："
        "1. 每次只提 1 个最关键的问题。"
        "2. 问题必须是封闭式的（答案只能是 是/否/不完全是）。不允许出现为什么，怎么回事等无法用是和否回答的问题。"
        "3. 根据 [History] 中的反馈不断修正推理。"
        "4. 当你确信已掌握全貌时，请必须以 `[SOLVED]` 开头，然后完整讲述还原的故事。"
        "5. **重要：严禁输出任何分析、前言或自我解释。直接输出问题或以 [SOLVED] 开头的真相。**"
    )
    
    user_prompt = f"""
    [起因 (Start)]: {start}
    [结果 (End)]: {end}
    
    [History / Clues]:
    """
    
    for h in history:
        score = h.get("score", 0.5)
        # Convert 0-1 score to human readable hint
        # 0.0-0.2: 完全错误/无关
        # 0.2-0.4: 偏离方向
        # 0.4-0.6: 尚不明确
        # 0.6-0.8: 有点沾边
        # 0.8-1.0: 非常接近/正确!
        
        hint = ""
        if score < 0.2: hint = "❌ 完全错误"
        elif score < 0.4: hint = "✖️ 偏离"
        elif score < 0.6: hint = "❓ 不确定"
        elif score < 0.8: hint = "✔️ 比较接近"
        else: hint = "✅ 正确/关键"
        
        user_prompt += f"- 猜想：{h.get('text')} => 反馈值: {score:.2f} ({hint})\n"
        
    # Check Max Rounds - REMOVED per user request to allow infinite play
    # current_round = len(history)
    # if current_round >= MAX_DETECTIVE_ROUNDS:
    #     user_prompt += f"\n【强制指令】已达到最大轮数限制 ({MAX_DETECTIVE_ROUNDS}轮)。请立即停止提问，直接以 `[SOLVED]` 开头，完整还原整个故事的真相。"
    # else:
    user_prompt += "\n【强制指令】请直接输出下一个封闭式问题，或者如果已确信真相，输出 `[SOLVED]` 开头的故事还原。不要输出任何寒暄或分析过程。"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print(f"\n====== [Detective] Incoming Request ======")
    print(f"Provider: {provider}")
    print(f"History Count: {len(history)}")
    print(f"--- [System Prompt] ---\n{sys_prompt}\n-----------------------")
    print(f"--- [User Prompt] ---\n{user_prompt}\n---------------------")

    try:
        response = ""
        if provider == "gemini":
            response = _call_gemini(messages, temperature=0.7, config=config)
        else:
            # Default to DeepSeek logic (compatible with OpenAI)
            response = _call_deepseek(messages, stream=False, temperature=1.0, model=LLM_MODEL_REASONING, config=config)
            
        print(f"====== [Detective] Response ======")
        print(response)
        print(f"====================================\n")
        return response
    except Exception as e:
        print(f"Detective failed: {e}")
        return f"侦探正在思考（Error: {str(e)}）..."

def reveal_truth(start: str, end: str, history: List[Dict], config: Dict = {}) -> str:
    """
    强制揭露真相（Reveal Truth / Restore Story）
    """
    provider = config.get("provider") or LLM_PROVIDER
    
    # Simply reuse the detective logic but with a forced instruction in the prompt
    # We construct a prompt that demands the solution immediately.
    
    sys_prompt = (
        "你是一名海龟汤上帝/侧写师。"
        "玩家请求直接还原整个故事的真相。"
        "请根据【起因】、【结果】以及已有的【线索记录】，完整地讲述这个故事。"
        "1. 故事必须合乎逻辑，连接起因和结果。"
        "2. 必须包含关键的转折点（为什么起因会导致结果）。"
        "3. 直接输出故事内容，以 `[SOLVED]` 开头，不要有任何前言。"
    )
    
    user_prompt = f"""
    [起因 (Start)]: {start}
    [结果 (End)]: {end}
    
    [线索记录 (History)]:
    """
    for h in history:
        score = h.get("score", 0.5)
        user_prompt += f"- {h.get('text')} (置信度: {score:.2f})\n"
        
    user_prompt += "\n【强制指令】请立即还原整个故事真相。直接讲述故事。"

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = ""
        if provider == "gemini":
            response = _call_gemini(messages, temperature=0.8, config=config)
        else:
            response = _call_deepseek(messages, stream=False, temperature=1.0, model=LLM_MODEL_REASONING, config=config)
            
        print(f"[Reveal Truth] Response: {response[:100]}...")
        
        # Ensure it has the [SOLVED] tag for frontend parsing
        if not response.startswith("[SOLVED]"):
            response = "[SOLVED] " + response
            
        return response
    except Exception as e:
        print(f"Reveal failed: {e}")
        return f"[SOLVED] 无法还原故事（Error: {str(e)}）"
