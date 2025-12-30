"""飞书相关API"""
from fastapi import APIRouter, Query
import logging

from ..services.feishu_service import feishu_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/jsapi_ticket")
async def get_jsapi_ticket(url: str = Query(..., description="当前页面URL")):
    """获取JSSDK鉴权配置"""
    try:
        ticket = await feishu_service.get_jsapi_ticket()
        config = feishu_service.generate_signature(ticket, url)

        logger.info(f"生成JSSDK配置: url={url}")
        return config

    except Exception as e:
        logger.error(f"获取jsapi_ticket失败: {e}")
        return {"error": str(e)}
