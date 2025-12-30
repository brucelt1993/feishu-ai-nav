"""飞书服务封装"""
import time
import hashlib
import httpx
import logging
from typing import Optional
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FeishuService:
    """飞书API服务"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self):
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self._token_cache: dict = {}
        self._ticket_cache: dict = {}

    async def get_tenant_access_token(self) -> str:
        """获取tenant_access_token，带缓存"""
        cache_key = "tenant_token"

        # 检查缓存
        if cache_key in self._token_cache:
            cache = self._token_cache[cache_key]
            if time.time() < cache["expire_time"]:
                return cache["token"]

        # 请求新token
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal/"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取tenant_access_token失败: {data}")
                raise Exception(f"获取token失败: {data.get('msg')}")

            token = data["tenant_access_token"]
            expire = data.get("expire", 7200)

            # 缓存（提前5分钟过期）
            self._token_cache[cache_key] = {
                "token": token,
                "expire_time": time.time() + expire - 300,
            }

            logger.info("获取tenant_access_token成功")
            return token

    async def get_jsapi_ticket(self) -> str:
        """获取jsapi_ticket"""
        cache_key = "jsapi_ticket"

        # 检查缓存
        if cache_key in self._ticket_cache:
            cache = self._ticket_cache[cache_key]
            if time.time() < cache["expire_time"]:
                return cache["ticket"]

        token = await self.get_tenant_access_token()
        url = f"{self.BASE_URL}/jssdk/ticket/get"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={},
            )
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取jsapi_ticket失败: {data}")
                raise Exception(f"获取ticket失败: {data.get('msg')}")

            ticket = data["data"]["ticket"]
            expire = data["data"].get("expire_in", 7200)

            # 缓存
            self._ticket_cache[cache_key] = {
                "ticket": ticket,
                "expire_time": time.time() + expire - 300,
            }

            logger.info("获取jsapi_ticket成功")
            return ticket

    def generate_signature(self, ticket: str, url: str) -> dict:
        """生成JSSDK签名"""
        import secrets

        timestamp = int(time.time() * 1000)
        noncestr = secrets.token_hex(16)

        # 签名字符串拼接顺序：jsapi_ticket, noncestr, timestamp, url
        verify_str = f"jsapi_ticket={ticket}&noncestr={noncestr}&timestamp={timestamp}&url={url}"
        signature = hashlib.sha1(verify_str.encode("utf-8")).hexdigest()

        return {
            "appId": self.app_id,
            "timestamp": timestamp,
            "nonceStr": noncestr,
            "signature": signature,
        }

    async def get_user_access_token(self, code: str) -> dict:
        """通过code获取user_access_token"""
        url = f"{self.BASE_URL}/authen/v2/oauth/token"
        # OAuth v2 需要用表单格式，参数名是 client_id/client_secret
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.app_id,
            "client_secret": self.app_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=payload,  # 用 data 而不是 json
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            data = response.json()

            if "error" in data:
                logger.error(f"获取user_access_token失败: {data}")
                raise Exception(f"登录失败: {data.get('error_description')}")

            return data

    async def get_user_info(self, user_access_token: str) -> dict:
        """获取用户信息"""
        url = f"{self.BASE_URL}/authen/v1/user_info"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {user_access_token}"},
            )
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取用户信息失败: {data}")
                raise Exception(f"获取用户信息失败: {data.get('msg')}")

            return data["data"]

    async def send_card_message(self, chat_id: str, card: dict):
        """发送卡片消息到群"""
        token = await self.get_tenant_access_token()
        url = f"{self.BASE_URL}/im/v1/messages?receive_id_type=chat_id"

        payload = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": str(card) if isinstance(card, dict) else card,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"发送消息失败: {data}")
                raise Exception(f"发送消息失败: {data.get('msg')}")

            logger.info(f"消息发送成功: {chat_id}")
            return data


# 单例
feishu_service = FeishuService()
