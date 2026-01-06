"""
飞书客户端
封装飞书 API 调用
"""

import json
import time
from typing import Any, Optional

import httpx
from loguru import logger

from app.config import settings


class FeishuClient:
    """飞书 API 客户端"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self):
        self._tenant_access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def _get_tenant_access_token(self) -> str:
        """获取企业级 access_token"""
        # 检查缓存
        if self._tenant_access_token and time.time() < self._token_expires_at:
            return self._tenant_access_token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                },
            )
            data = resp.json()

            if data.get("code") != 0:
                logger.error(f"❌ 获取 tenant_access_token 失败: {data}")
                raise Exception(f"获取 token 失败: {data.get('msg')}")

            self._tenant_access_token = data["tenant_access_token"]
            # 提前 5 分钟过期
            self._token_expires_at = time.time() + data.get("expire", 7200) - 300

            logger.debug("✅ 获取 tenant_access_token 成功")
            return self._tenant_access_token

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """发送 API 请求"""
        token = await self._get_tenant_access_token()

        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method=method,
                url=f"{self.BASE_URL}{path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json=json_data,
                params=params,
            )

            return resp.json()

    async def send_text(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> Optional[str]:
        """
        发送文本消息

        Args:
            chat_id: 会话 ID
            text: 文本内容
            reply_to: 回复的消息 ID

        Returns:
            消息 ID
        """
        content = json.dumps({"text": text})

        body = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": content,
        }

        # 添加回复
        if reply_to:
            body["reply_in_thread"] = False

        result = await self._request(
            "POST",
            "/im/v1/messages",
            json_data=body,
            params={"receive_id_type": "chat_id"},
        )

        if result.get("code") != 0:
            logger.error(f"❌ 发送消息失败: {result}")
            return None

        message_id = result.get("data", {}).get("message_id")
        logger.debug(f"✅ 发送消息成功: {message_id}")
        return message_id

    async def send_reply(
        self,
        chat_id: str,
        message_id: str,
        content: str,
    ):
        """
        回复消息

        Args:
            chat_id: 会话 ID
            message_id: 要回复的消息 ID
            content: 回复内容
        """
        body = {
            "content": json.dumps({"text": content}),
            "msg_type": "text",
        }

        result = await self._request(
            "POST",
            f"/im/v1/messages/{message_id}/reply",
            json_data=body,
        )

        if result.get("code") != 0:
            logger.error(f"❌ 回复消息失败: {result}")
            return None

        return result.get("data", {}).get("message_id")

    async def update_message(
        self,
        message_id: str,
        text: str,
    ):
        """
        更新消息内容

        Args:
            message_id: 消息 ID
            text: 新的文本内容
        """
        body = {
            "content": json.dumps({"text": text}),
        }

        result = await self._request(
            "PATCH",
            f"/im/v1/messages/{message_id}",
            json_data=body,
        )

        if result.get("code") != 0:
            logger.error(f"❌ 更新消息失败: {result}")

    async def send_card(
        self,
        chat_id: str,
        card: dict[str, Any],
        reply_to: Optional[str] = None,
    ) -> Optional[str]:
        """
        发送卡片消息

        Args:
            chat_id: 会话 ID
            card: 卡片内容 (飞书卡片 JSON)
            reply_to: 回复的消息 ID

        Returns:
            消息 ID
        """
        body = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card),
        }

        result = await self._request(
            "POST",
            "/im/v1/messages",
            json_data=body,
            params={"receive_id_type": "chat_id"},
        )

        if result.get("code") != 0:
            logger.error(f"❌ 发送卡片失败: {result}")
            return None

        message_id = result.get("data", {}).get("message_id")
        logger.debug(f"✅ 发送卡片成功: {message_id}")
        return message_id

    async def update_card(
        self,
        message_id: str,
        card: dict[str, Any],
    ):
        """
        更新卡片消息

        Args:
            message_id: 消息 ID
            card: 新的卡片内容
        """
        body = {
            "content": json.dumps(card),
        }

        result = await self._request(
            "PATCH",
            f"/im/v1/messages/{message_id}",
            json_data=body,
        )

        if result.get("code") != 0:
            logger.error(f"❌ 更新卡片失败: {result}")
