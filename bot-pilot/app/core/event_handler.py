"""
事件处理器
负责分发和处理飞书事件
"""

import asyncio
import json
from typing import Any

from loguru import logger

from app.core.message_handler import MessageHandler


class EventHandler:
    """飞书事件处理器"""

    def __init__(self):
        self.message_handler = MessageHandler()
        # 事件去重 (防止飞书重复推送)
        self._processed_events: set[str] = set()
        self._max_cache_size = 1000

    def _is_duplicate(self, event_id: str) -> bool:
        """检查事件是否重复"""
        if event_id in self._processed_events:
            logger.debug(f"⏭️ 重复事件，跳过: {event_id}")
            return True

        self._processed_events.add(event_id)

        # 缓存清理
        if len(self._processed_events) > self._max_cache_size:
            # 简单清理：保留一半
            to_remove = list(self._processed_events)[: self._max_cache_size // 2]
            for item in to_remove:
                self._processed_events.discard(item)

        return False

    async def handle_message(self, event: dict[str, Any]):
        """
        处理 v2.0 消息事件
        im.message.receive_v1
        """
        message = event.get("message", {})
        message_id = message.get("message_id", "")

        # 去重检查
        if self._is_duplicate(message_id):
            return

        # 提取消息信息
        chat_id = message.get("chat_id", "")
        chat_type = message.get("chat_type", "")  # p2p / group
        message_type = message.get("message_type", "")  # text / post / image...
        content_str = message.get("content", "{}")

        # 发送者信息
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {})
        open_id = sender_id.get("open_id", "")
        user_id = sender_id.get("user_id", "")

        # 提及信息 (@机器人)
        mentions = message.get("mentions", [])

        logger.info(
            f"💬 收到消息 | 类型: {chat_type} | 消息类型: {message_type} | "
            f"发送者: {open_id[:10]}..."
        )

        # 解析消息内容
        try:
            content = json.loads(content_str)
        except json.JSONDecodeError:
            content = {"text": content_str}

        # 构建统一消息结构
        msg_data = {
            "message_id": message_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "message_type": message_type,
            "content": content,
            "open_id": open_id,
            "user_id": user_id,
            "mentions": mentions,
            "raw_event": event,
        }

        # 异步处理消息 (快速返回响应)
        asyncio.create_task(self._process_message(msg_data))

    async def _process_message(self, msg_data: dict[str, Any]):
        """异步处理消息"""
        try:
            await self.message_handler.handle(msg_data)
        except Exception as e:
            logger.error(f"❌ 消息处理异常: {e}")
            # 发送错误提示给用户
            await self.message_handler.send_error_reply(
                msg_data["chat_id"], msg_data["message_id"], str(e)
            )

    async def handle_message_v1(self, event: dict[str, Any]):
        """
        处理 v1.0 消息事件 (兼容旧版本)
        """
        # v1 格式转换为 v2 格式
        msg_data = {
            "message_id": event.get("msg_id", event.get("message_id", "")),
            "chat_id": event.get("open_chat_id", ""),
            "chat_type": "group" if event.get("open_chat_id") else "p2p",
            "message_type": event.get("msg_type", "text"),
            "content": {"text": event.get("text", "")},
            "open_id": event.get("open_id", ""),
            "user_id": event.get("user_id", ""),
            "mentions": [],
            "raw_event": event,
        }

        asyncio.create_task(self._process_message(msg_data))
