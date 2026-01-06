"""
MCP 工具执行器
将工具调用桥接到实际的服务
"""

from typing import Any

from loguru import logger

from app.services.stats_bridge import StatsBridge


class ToolExecutor:
    """工具执行器"""

    def __init__(self):
        self.stats = StatsBridge()
        # 工具映射
        self._handlers = {
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
        }

    async def execute(self, function_name: str, arguments: dict[str, Any]) -> Any:
        """
        执行工具

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

        try:
            result = await handler(**arguments)
            logger.info(f"✅ 工具执行成功: {function_name}")
            return result
        except Exception as e:
            logger.error(f"❌ 工具执行失败 {function_name}: {e}")
            return {"error": str(e)}

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
