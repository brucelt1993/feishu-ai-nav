"""消息推送服务"""
from datetime import datetime
import logging

from .feishu_service import feishu_service
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PushService:
    """推送服务"""

    async def push_daily_report(self, report: dict):
        """推送每日统计报告到飞书群"""
        if not settings.push_chat_id:
            logger.warning("未配置推送群ID，跳过推送")
            return False

        try:
            card = self._build_report_card(report)
            await feishu_service.send_card_message(settings.push_chat_id, card)
            logger.info("每日报告推送成功")
            return True
        except Exception as e:
            logger.error(f"推送每日报告失败: {e}")
            return False

    def _build_report_card(self, report: dict) -> dict:
        """构建报告卡片消息"""
        date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))

        # 构建工具排行文本
        tool_ranking = report.get("tool_ranking", [])
        tool_text = "\n".join([
            f"{i+1}. {t['name']} - {t['click_count']}次"
            for i, t in enumerate(tool_ranking[:5])
        ]) or "暂无数据"

        # 构建用户排行文本
        user_ranking = report.get("user_ranking", [])
        user_text = "\n".join([
            f"{i+1}. {u['name']} - {u['click_count']}次"
            for i, u in enumerate(user_ranking[:5])
        ]) or "暂无数据"

        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"content": f"📊 AI工具使用日报 - {date_str}", "tag": "plain_text"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"""**📈 昨日数据概览**
• PV（页面浏览量）: **{report.get('pv', 0)}**
• UV（独立用户数）: **{report.get('uv', 0)}**
• 新增用户: **{report.get('new_users', 0)}**"""
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🔥 工具使用TOP5**\n{tool_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**👥 活跃用户TOP5**\n{user_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看详情"},
                            "type": "primary",
                            "url": settings.app_base_url + "/admin" if settings.app_base_url else "#"
                        }
                    ]
                }
            ]
        }

        return card


push_service = PushService()
