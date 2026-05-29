import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 1) 读取 .env 文件，把里面的 KEY=VALUE 加到环境变量里
#    这样 os.getenv("XXX") 才能拿到你本地配置
#    注意：load_dotenv() 默认找当前工作目录下的 .env（也会向上找）
load_dotenv()


@dataclass
class Settings:
    """
    这个 Settings 用来集中管理“配置项”（路径、密钥、服务地址等）。
    dataclass 的好处是：写起来像定义变量，但会自动生成 __init__、repr 等。
    """

    # ========== 路径配置 ==========
    # 项目根目录：backend/（按你队友的约定）
    # __file__ 是当前 config.py 的路径
    # os.path.dirname(__file__) -> 当前文件所在目录
    # 然后往上两级 "..", ".." 得到 backend/ 根目录
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # data 目录：backend/data
    DATA_DIR: str = os.path.join(BASE_DIR, "data")

    # 存故事的 JSON 文件：backend/data/stories.json
    # 你项目里很可能用它做“简易数据库”
    STORIES_PATH: str = os.path.join(DATA_DIR, "stories.json")

    # ========== 大模型（LLM）配置 ==========
    # 这三个是“占位配置”，用于接不同的大模型服务
    # 比如：openai / deepseek / azure / mock 等

    # 用哪个 provider，默认 mock（也就是不用真实调用大模型）
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")

    # 大模型 API KEY（从环境变量读取；如果没有就是空字符串）
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

    # 大模型的 base url（有些 provider 需要自定义）
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")


# 生成一个全局单例 settings
# 项目其它地方一般会这样用：
#   from app.core.config import settings
#   print(settings.STORIES_PATH)
settings = Settings()
