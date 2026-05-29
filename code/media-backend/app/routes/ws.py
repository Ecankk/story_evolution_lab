from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.scoring import score_turns
from app.services.storage import append_turns
from app.services.llm_proxy import stream_ai_turns

router = APIRouter()


@router.websocket("/ws/story/{story_id}")
async def ws_story(websocket: WebSocket, story_id: str):
    """
    WebSocket 版本的“继续故事”。

    URL:
      /ws/story/{story_id}

    前端发送（JSON）:
      {
        "user_text": "xxx",
        "rounds": 1,
        "mode": "human_ai"
      }

    后端推送（JSON）:
      每次推送一条“turn”对象（通常包含 author/text/turn/x/y/flow_score/entropy_score...）
      因为 append_turns 返回 list，所以这里 send_json(saved_*[0]) 只推其中一条
    """

    # 1) 接受 WebSocket 握手
    #    一旦 accept 了，连接就建立成功了
    await websocket.accept()

    try:
        # 2) 持续监听前端发来的消息（一个连接里可以发多次）
        while True:
            # 等待前端发 JSON（如果发的是文本/不是 JSON，会抛异常）
            payload = await websocket.receive_json()

            # 从 payload 拿参数，做一些兜底
            user_text = (payload.get("user_text") or "").strip()
            rounds = int(payload.get("rounds") or 1)
            mode = payload.get("mode") or "human_ai"

            # ---------------------------
            # 3) 先处理 human turn (仅当有文本时)
            # ---------------------------
            if user_text:
                # 组装 human turn（注意：这里只包含 author/text；没有 story_id/turn/x/y）
                human_turn = {"author": "human", "text": user_text}

                # score_turns：给 turn 计算指标（embedding、flow_score、entropy_score、x/y等）
                # 输入是 list，所以这里传 [human_turn]
                scored_human = score_turns(story_id, [human_turn])

                # append_turns：把打分后的 turn 存到 stories.json（或别的存储），并分配 turn 编号
                # append_turns 设计为返回 list（因为可能一次 append 多条）
                saved_human = append_turns(story_id, scored_human)

                # 推送给前端：只推第一条（human turn 只有一条，所以 [0] 没问题）
                await websocket.send_json(saved_human[0])

            # ---------------------------
            # 4) 再处理 AI turns（流式）
            # ---------------------------

            # stream_ai_turns 是 async generator：
            # 它会逐条 yield ai_turn（每条是 {"author":"ai","text":"..."}）
            async for ai_turn in stream_ai_turns(story_id, user_text, rounds, mode):

                # 每条 AI turn 都走同样的“打分->存储->推送”流程
                scored_ai = score_turns(story_id, [ai_turn])
                saved_ai = append_turns(story_id, scored_ai)

                # 推送给前端：同样只推第一条
                await websocket.send_json(saved_ai[0])

    except WebSocketDisconnect:
        # 5) 前端主动断开连接（比如刷新页面/关闭标签页）会触发这里
        return

    except Exception:
        # 6) 兜底：任何异常都尝试关闭连接，避免服务端一直报错
        #    （比如 payload 不是 JSON、score_turns 抛错等）
        try:
            await websocket.close()
        except Exception:
            pass
