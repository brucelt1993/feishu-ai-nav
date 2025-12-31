"""点击服务 - 防刷数"""
from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)

# 缓存：最多10000条记录，60秒过期
# key: "user_id:tool_id" 或 "ip:tool_id"（匿名用户）
_click_cache: TTLCache = TTLCache(maxsize=10000, ttl=60)


def should_record_click(user_id: int | None, tool_id: int, ip_address: str | None) -> bool:
    """
    检查是否应该记录点击（防刷）

    策略：同一用户/IP + 工具，60秒内只计1次

    Args:
        user_id: 用户ID（登录用户）
        tool_id: 工具ID
        ip_address: IP地址（匿名用户用）

    Returns:
        True: 应该记录（首次点击或已过60秒）
        False: 不应记录（60秒内重复点击）
    """
    # 构建缓存key：优先用user_id，否则用ip
    if user_id:
        cache_key = f"u:{user_id}:{tool_id}"
    elif ip_address:
        cache_key = f"ip:{ip_address}:{tool_id}"
    else:
        # 无法识别用户，直接记录
        return True

    # 检查缓存
    if cache_key in _click_cache:
        logger.debug(f"点击去重: {cache_key} 已存在，跳过记录")
        return False

    # 写入缓存
    _click_cache[cache_key] = True
    logger.debug(f"点击记录: {cache_key}")
    return True


def get_cache_stats() -> dict:
    """获取缓存统计信息（调试用）"""
    return {
        "size": len(_click_cache),
        "maxsize": _click_cache.maxsize,
        "ttl": _click_cache.ttl,
    }
