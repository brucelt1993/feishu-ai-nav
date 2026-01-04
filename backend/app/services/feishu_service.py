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

            logger.info(f"OAuth返回数据: {data}")
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

    async def send_card_message(self, receive_id: str, card: dict, receive_id_type: str = "chat_id"):
        """发送卡片消息"""
        import json
        token = await self.get_tenant_access_token()
        url = f"{self.BASE_URL}/im/v1/messages?receive_id_type={receive_id_type}"

        # 确保 card 是 JSON 字符串格式
        content = json.dumps(card) if isinstance(card, dict) else card

        payload = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": content,
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

            logger.info(f"消息发送成功: {receive_id}")
            return data

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """通过邮箱获取用户信息"""
        token = await self.get_tenant_access_token()
        url = f"{self.BASE_URL}/contact/v3/users/batch_get_id"

        payload = {
            "emails": [email],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                params={"user_id_type": "open_id"},
            )
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"通过邮箱获取用户失败: {data}")
                return None

            user_list = data.get("data", {}).get("user_list", [])
            if user_list and user_list[0].get("user_id"):
                return {"open_id": user_list[0]["user_id"]}

            return None

    async def send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        content: str,
        attachment_name: str,
        attachment_content: bytes
    ):
        """发送带附件的邮件（通过飞书机器人发送文件消息）"""
        import base64

        # 先获取用户的 open_id
        user_info = await self.get_user_by_email(to_email)
        if not user_info or not user_info.get("open_id"):
            raise Exception(f"未找到邮箱对应的飞书用户: {to_email}")

        open_id = user_info["open_id"]

        # 先上传文件
        token = await self.get_tenant_access_token()

        # 使用飞书文件上传API
        upload_url = f"{self.BASE_URL}/im/v1/files"

        # 创建表单数据
        import io
        files = {
            "file": (attachment_name, io.BytesIO(attachment_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }
        form_data = {
            "file_type": "stream",
            "file_name": attachment_name,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                upload_url,
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data=form_data,
            )
            upload_data = response.json()

            if upload_data.get("code") != 0:
                logger.error(f"上传文件失败: {upload_data}")
                raise Exception(f"上传文件失败: {upload_data.get('msg')}")

            file_key = upload_data["data"]["file_key"]

        # 发送文件消息
        import json
        msg_url = f"{self.BASE_URL}/im/v1/messages?receive_id_type=open_id"
        msg_payload = {
            "receive_id": open_id,
            "msg_type": "file",
            "content": json.dumps({"file_key": file_key}),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                msg_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=msg_payload,
            )
            msg_data = response.json()

            if msg_data.get("code") != 0:
                logger.error(f"发送文件消息失败: {msg_data}")
                raise Exception(f"发送文件消息失败: {msg_data.get('msg')}")

            logger.info(f"文件消息发送成功: {to_email}")
            return msg_data


# 单例
feishu_service = FeishuService()
