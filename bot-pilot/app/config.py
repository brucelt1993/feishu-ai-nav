"""
Bot-Pilot 配置管理
使用 pydantic-settings 从环境变量加载配置
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 服务配置
    bot_port: int = 8001
    log_level: str = "INFO"
    debug: bool = False

    # 飞书配置
    feishu_app_id: str
    feishu_app_secret: str
    feishu_encrypt_key: Optional[str] = None  # 事件加密密钥
    feishu_verification_token: Optional[str] = None  # 事件验证 Token

    # OpenAI 配置
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7

    # 数据库配置 (复用现有)
    database_url: str

    # 机器人行为配置
    bot_name: str = "AI导航小助手"
    max_context_messages: int = 10  # 上下文记忆消息数
    thinking_message: str = "🤔 思考中..."  # 思考中提示

    @property
    def is_sqlite(self) -> bool:
        """判断是否使用 SQLite"""
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
