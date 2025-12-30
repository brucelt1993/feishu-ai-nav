"""应用配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    # 飞书配置
    feishu_app_id: str = ""
    feishu_app_secret: str = ""

    # 数据库配置
    database_url: str = "postgresql://aiuser:aipass123@localhost:5432/ai_nav"

    # 管理员配置
    admin_open_ids: str = ""  # 逗号分隔的open_id列表

    # 推送配置
    push_chat_id: str = ""
    push_cron: str = "0 9 * * *"

    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    app_base_url: str = ""  # 应用访问地址，用于卡片消息链接

    @property
    def admin_list(self) -> list[str]:
        """获取管理员列表"""
        if not self.admin_open_ids:
            return []
        return [x.strip() for x in self.admin_open_ids.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
