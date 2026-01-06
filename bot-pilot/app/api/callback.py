"""
飞书事件回调接口
处理机器人消息事件
"""

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Header, Request
from loguru import logger

from app.config import settings
from app.core.event_handler import EventHandler

router = APIRouter()

# 事件处理器
event_handler = EventHandler()


def verify_signature(timestamp: str, nonce: str, body: bytes, signature: str) -> bool:
    """验证飞书请求签名"""
    if not settings.feishu_encrypt_key:
        return True  # 未配置加密密钥，跳过验证

    content = f"{timestamp}{nonce}{settings.feishu_encrypt_key}{body.decode('utf-8')}"
    calculated = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return calculated == signature


@router.post("/callback")
async def feishu_callback(
    request: Request,
    x_lark_request_timestamp: str = Header(None, alias="X-Lark-Request-Timestamp"),
    x_lark_request_nonce: str = Header(None, alias="X-Lark-Request-Nonce"),
    x_lark_signature: str = Header(None, alias="X-Lark-Signature"),
):
    """
    飞书事件回调入口
    处理：URL验证、消息事件、其他事件
    """
    body = await request.body()

    # 签名验证
    if x_lark_signature and not verify_signature(
        x_lark_request_timestamp or "",
        x_lark_request_nonce or "",
        body,
        x_lark_signature,
    ):
        logger.warning("❌ 签名验证失败")
        return {"code": 401, "msg": "signature verification failed"}

    # 解析请求体
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error("❌ JSON 解析失败")
        return {"code": 400, "msg": "invalid json"}

    logger.debug(f"📨 收到飞书事件: {json.dumps(data, ensure_ascii=False)[:500]}")

    # 1. URL 验证 (机器人配置时的挑战)
    if "challenge" in data:
        logger.info("🔐 URL 验证请求")
        return {"challenge": data["challenge"]}

    # 2. 事件回调 (v2.0 格式)
    if "header" in data:
        return await handle_event_v2(data)

    # 3. 事件回调 (v1.0 格式，兼容)
    if "event" in data:
        return await handle_event_v1(data)

    return {"code": 0, "msg": "ok"}


async def handle_event_v2(data: dict[str, Any]) -> dict:
    """
    处理 v2.0 格式事件
    """
    header = data.get("header", {})
    event_type = header.get("event_type", "")
    event_id = header.get("event_id", "")

    logger.info(f"📬 事件类型: {event_type}, ID: {event_id}")

    # 消息接收事件
    if event_type == "im.message.receive_v1":
        event = data.get("event", {})
        await event_handler.handle_message(event)
        return {"code": 0, "msg": "ok"}

    # 其他事件类型可在此扩展
    logger.info(f"⏭️ 未处理的事件类型: {event_type}")
    return {"code": 0, "msg": "ok"}


async def handle_event_v1(data: dict[str, Any]) -> dict:
    """
    处理 v1.0 格式事件 (兼容)
    """
    event = data.get("event", {})
    event_type = data.get("type", "")

    logger.info(f"📬 [v1] 事件类型: {event_type}")

    if event_type == "message":
        await event_handler.handle_message_v1(event)
        return {"code": 0, "msg": "ok"}

    return {"code": 0, "msg": "ok"}
