"""
MCP 工具执行器
将工具调用桥接到实际的服务
"""

import asyncio
import json
import traceback
from typing import Any

from loguru import logger
from sqlalchemy.exc import InterfaceError, OperationalError, DBAPIError

from app.services.stats_bridge import StatsBridge
from app.services.database import engine

# 数据库连接错误重试配置
MAX_RETRIES = 2
RETRY_DELAY = 0.5  # 秒


def _is_connection_error(e: Exception) -> bool:
    """判断是否是数据库连接错误"""
    error_msg = str(e).lower()
    connection_keywords = [
        "connection is closed",
        "connection was closed",
        "connection reset",
        "connection refused",
        "broken pipe",
        "server closed the connection",
    ]
    return any(kw in error_msg for kw in connection_keywords)


class ToolExecutor:
    """工具执行器"""

    def __init__(self):
        self.stats = StatsBridge()
        # 工具映射
        self._handlers = {
            # 原有工具
            "get_overview": self._get_overview,
            "get_tool_ranking": self._get_tool_ranking,
            "get_user_ranking": self._get_user_ranking,
            "get_trend": self._get_trend,
            "get_tool_detail": self._get_tool_detail,
            "get_feedback_summary": self._get_feedback_summary,
            "search_tools": self._search_tools,
            "get_category_stats": self._get_category_stats,
            "get_retention_stats": self._get_retention_stats,
            "get_hourly_distribution": self._get_hourly_distribution,
            # 新增工具
            "get_provider_stats": self._get_provider_stats,
            "get_tool_interactions": self._get_tool_interactions,
            "get_hot_tools": self._get_hot_tools,
            "get_want_list": self._get_want_list,
            "get_search_keywords": self._get_search_keywords,
            "recommend_by_scenario": self._recommend_by_scenario,
        }

    async def execute(self, function_name: str, arguments: dict[str, Any]) -> Any:
        """
        执行工具（带重试机制）

        Args:
            function_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        handler = self._handlers.get(function_name)
        if not handler:
            logger.warning(f"⚠️ 未知工具: {function_name}")
            return {"error": f"Unknown tool: {function_name}"}

        # 带重试的执行
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = await handler(**arguments)
                # 打印返回结果（截断过长内容）
                result_str = json.dumps(result, ensure_ascii=False, default=str)
                if len(result_str) > 500:
                    result_preview = result_str[:500] + f"... (共{len(result_str)}字符)"
                else:
                    result_preview = result_str
                logger.info(f"✅ 工具执行成功: {function_name}, 返回: {result_preview}")
                return result
            except (InterfaceError, OperationalError, DBAPIError) as e:
                # 数据库错误，检查是否是连接问题
                if _is_connection_error(e):
                    last_error = e
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            f"⚠️ 数据库连接断开，重试中 ({attempt + 1}/{MAX_RETRIES}): {e}"
                        )
                        await asyncio.sleep(RETRY_DELAY)
                        # 清理连接池中的无效连接
                        await engine.dispose()
                    else:
                        logger.error(f"❌ 数据库连接错误，重试已用尽: {e}")
                else:
                    # 其他数据库错误，不重试
                    logger.error(f"❌ 数据库错误 {function_name}: {e}")
                    return {"error": str(e)}
            except Exception as e:
                # 检查是否是 asyncpg 的连接错误（可能未被 SQLAlchemy 包装）
                if _is_connection_error(e):
                    last_error = e
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            f"⚠️ 连接错误，重试中 ({attempt + 1}/{MAX_RETRIES}): {e}"
                        )
                        await asyncio.sleep(RETRY_DELAY)
                        await engine.dispose()
                    else:
                        logger.error(f"❌ 连接错误，重试已用尽: {e}")
                else:
                    logger.error(f"❌ 工具执行失败 {function_name}: {e}")
                    logger.error(f"堆栈: {traceback.format_exc()}")
                    return {"error": str(e)}

        return {"error": f"数据库连接失败: {last_error}"}

    async def _get_overview(self) -> dict:
        """获取今日概览"""
        return await self.stats.get_overview()

    async def _get_tool_ranking(self, days: int = 7, limit: int = 10) -> dict:
        """获取工具排行"""
        return await self.stats.get_tool_ranking(days=days, limit=limit)

    async def _get_user_ranking(self, days: int = 7, limit: int = 10) -> dict:
        """获取用户排行"""
        return await self.stats.get_user_ranking(days=days, limit=limit)

    async def _get_trend(self, days: int = 30) -> dict:
        """获取访问趋势"""
        return await self.stats.get_trend(days=days)

    async def _get_tool_detail(self, tool_name: str) -> dict:
        """获取工具详情"""
        return await self.stats.get_tool_detail(tool_name=tool_name)

    async def _get_feedback_summary(self, days: int = 30, limit: int = 20) -> dict:
        """获取反馈汇总"""
        return await self.stats.get_feedback_summary(days=days, limit=limit)

    async def _search_tools(self, keyword: str, category: str = None) -> dict:
        """搜索工具"""
        return await self.stats.search_tools(keyword=keyword, category=category)

    async def _get_category_stats(self, days: int = 7) -> dict:
        """获取分类统计"""
        return await self.stats.get_category_stats(days=days)

    async def _get_retention_stats(self, period: str = "day") -> dict:
        """获取留存分析"""
        return await self.stats.get_retention_stats(period=period)

    async def _get_hourly_distribution(self, days: int = 7) -> dict:
        """获取时段分布"""
        return await self.stats.get_hourly_distribution(days=days)

    # ========== 新增工具 ==========

    async def _get_provider_stats(self, days: int = 7, limit: int = 10) -> dict:
        """获取提供者统计"""
        return await self.stats.get_provider_stats(days=days, limit=limit)

    async def _get_tool_interactions(self, limit: int = 10) -> dict:
        """获取工具互动排行"""
        return await self.stats.get_tool_interactions(limit=limit)

    async def _get_hot_tools(self, days: int = 7, limit: int = 10) -> dict:
        """获取热门新工具"""
        return await self.stats.get_hot_tools(days=days, limit=limit)

    async def _get_want_list(self, days: int = 30, limit: int = 20) -> dict:
        """获取用户想要的工具"""
        return await self.stats.get_want_list(days=days, limit=limit)

    async def _get_search_keywords(self, days: int = 7, limit: int = 20) -> dict:
        """获取搜索热词"""
        return await self.stats.get_search_keywords(days=days, limit=limit)

    async def _recommend_by_scenario(self, scenario: str, limit: int = 5) -> dict:
        """根据场景推荐工具"""
        return await self.stats.recommend_by_scenario(scenario=scenario, limit=limit)
