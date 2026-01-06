"""
消息处理器
负责消息解析、意图识别、调用 LLM 并回复
"""

import re
from typing import Any

from loguru import logger

from app.config import settings
from app.llm.chat_service import ChatService
from app.services.feishu_client import FeishuClient


class MessageHandler:
    """消息处理器"""

    def __init__(self):
        self.feishu = FeishuClient()
        self.chat_service = ChatService()
        # 快捷命令映射
        self.commands = {
            "/help": self._cmd_help,
            "/今日数据": self._cmd_overview,
            "/工具排行": self._cmd_tool_ranking,
            "/用户排行": self._cmd_user_ranking,
        }

    async def handle(self, msg_data: dict[str, Any]):
        """处理消息"""
        chat_id = msg_data["chat_id"]
        chat_type = msg_data["chat_type"]
        message_type = msg_data["message_type"]
        content = msg_data["content"]
        message_id = msg_data["message_id"]
        open_id = msg_data["open_id"]
        mentions = msg_data.get("mentions", [])

        # 只处理文本消息
        if message_type != "text":
            logger.info(f"⏭️ 跳过非文本消息: {message_type}")
            return

        # 提取文本内容
        text = self._extract_text(content)
        if not text:
            return

        logger.info(f"📝 消息内容: {text}")

        # 群聊需要 @ 机器人才响应
        if chat_type == "group":
            if not self._is_mentioned(mentions):
                logger.debug("⏭️ 群聊消息未 @ 机器人，跳过")
                return
            # 移除 @ 部分
            text = self._remove_mentions(text)

        text = text.strip()
        if not text:
            return

        # 1. 检查是否是快捷命令
        for cmd, handler in self.commands.items():
            if text.startswith(cmd):
                await handler(chat_id, message_id, text, open_id)
                return

        # 2. 发送"思考中"提示
        thinking_msg_id = await self.feishu.send_text(
            chat_id, settings.thinking_message, reply_to=message_id
        )

        # 3. 调用 ChatService 处理
        try:
            response = await self.chat_service.chat(
                user_id=open_id,
                message=text,
                chat_id=chat_id,
            )

            # 4. 更新或发送回复
            if thinking_msg_id:
                await self.feishu.update_message(thinking_msg_id, response)
            else:
                await self.feishu.send_reply(chat_id, message_id, response)

        except Exception as e:
            logger.error(f"❌ ChatService 异常: {e}")
            error_text = "抱歉，处理消息时遇到了问题，请稍后再试。"
            if thinking_msg_id:
                await self.feishu.update_message(thinking_msg_id, error_text)
            else:
                await self.feishu.send_text(chat_id, error_text, reply_to=message_id)

    def _extract_text(self, content: dict) -> str:
        """从消息内容中提取文本"""
        # text 消息格式: {"text": "消息内容"}
        if "text" in content:
            return content["text"]
        return ""

    def _is_mentioned(self, mentions: list) -> bool:
        """检查是否 @ 了机器人"""
        if not mentions:
            return False
        # 检查 mentions 中是否包含机器人
        for mention in mentions:
            # 机器人的 id.open_id 以 "ou_" 开头
            # 或者 name 匹配机器人名称
            id_info = mention.get("id", {})
            if id_info.get("open_id", "").startswith("ou_"):
                # 这里简化处理，实际可以检查是否是本机器人
                return True
            # 也可能是 @ 全体
            if mention.get("key") == "@_all":
                return True
        return True  # 有 mentions 就认为是 @ 了

    def _remove_mentions(self, text: str) -> str:
        """移除 @ 部分"""
        # 飞书的 @ 格式可能是 @用户名 或者 at_user 标记
        # 简单处理：移除 @xxx 格式
        text = re.sub(r"@\S+\s*", "", text)
        return text.strip()

    async def send_error_reply(self, chat_id: str, message_id: str, error: str):
        """发送错误回复"""
        error_text = f"⚠️ 处理失败: {error[:100]}"
        await self.feishu.send_text(chat_id, error_text, reply_to=message_id)

    # ========== 快捷命令处理 ==========

    async def _cmd_help(self, chat_id: str, message_id: str, text: str, open_id: str):
        """帮助命令"""
        help_text = f"""👋 你好，我是 **{settings.bot_name}**！

🎯 **我能做什么**
- 回答 AI 导航平台相关问题
- 查询平台使用数据和统计报表
- 推荐合适的 AI 工具

📊 **快捷命令**
- `/今日数据` - 查看今日概览
- `/工具排行` - 热门工具 TOP10
- `/用户排行` - 活跃用户 TOP10
- `/help` - 显示帮助

💡 **使用方式**
- 私聊：直接发消息
- 群聊：@我 + 消息

有什么问题尽管问我！"""

        await self.feishu.send_text(chat_id, help_text, reply_to=message_id)

    async def _cmd_overview(self, chat_id: str, message_id: str, text: str, open_id: str):
        """今日数据概览"""
        # 调用 ChatService 触发 get_overview 工具
        await self.feishu.send_text(
            chat_id, settings.thinking_message, reply_to=message_id
        )
        response = await self.chat_service.chat(
            user_id=open_id,
            message="请查询今日数据概览",
            chat_id=chat_id,
        )
        await self.feishu.send_reply(chat_id, message_id, response)

    async def _cmd_tool_ranking(self, chat_id: str, message_id: str, text: str, open_id: str):
        """工具排行"""
        await self.feishu.send_text(
            chat_id, settings.thinking_message, reply_to=message_id
        )
        response = await self.chat_service.chat(
            user_id=open_id,
            message="请查询最近7天的工具排行榜",
            chat_id=chat_id,
        )
        await self.feishu.send_reply(chat_id, message_id, response)

    async def _cmd_user_ranking(self, chat_id: str, message_id: str, text: str, open_id: str):
        """用户排行"""
        await self.feishu.send_text(
            chat_id, settings.thinking_message, reply_to=message_id
        )
        response = await self.chat_service.chat(
            user_id=open_id,
            message="请查询最近7天的用户活跃排行榜",
            chat_id=chat_id,
        )
        await self.feishu.send_reply(chat_id, message_id, response)
