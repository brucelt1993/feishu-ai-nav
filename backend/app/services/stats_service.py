"""统计服务"""
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Tool, User, ClickLog
import logging

logger = logging.getLogger(__name__)


class StatsService:
    """统计服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self) -> dict:
        """获取统计概览"""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())

        # 今日PV
        today_pv_query = select(func.count(ClickLog.id)).where(
            ClickLog.clicked_at >= today_start
        )
        today_pv = (await self.db.execute(today_pv_query)).scalar() or 0

        # 今日UV
        today_uv_query = select(func.count(distinct(ClickLog.user_id))).where(
            ClickLog.clicked_at >= today_start
        )
        today_uv = (await self.db.execute(today_uv_query)).scalar() or 0

        # 总PV
        total_pv_query = select(func.count(ClickLog.id))
        total_pv = (await self.db.execute(total_pv_query)).scalar() or 0

        # 总UV
        total_uv_query = select(func.count(User.id))
        total_uv = (await self.db.execute(total_uv_query)).scalar() or 0

        # 工具总数
        tools_query = select(func.count(Tool.id)).where(Tool.is_active == True)
        total_tools = (await self.db.execute(tools_query)).scalar() or 0

        # 今日新增用户
        new_users_query = select(func.count(User.id)).where(
            User.first_visit_at >= today_start
        )
        new_users_today = (await self.db.execute(new_users_query)).scalar() or 0

        return {
            "today_pv": today_pv,
            "today_uv": today_uv,
            "total_clicks": total_pv,  # 总点击数
            "total_users": total_uv,   # 总用户数
            "total_tools": total_tools,
            "new_users_today": new_users_today,
        }

    async def get_tool_stats(self, days: int = 7, limit: int = 10) -> list[dict]:
        """获取工具使用排行"""
        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(
                Tool.id,
                Tool.name,
                func.count(ClickLog.id).label("click_count"),
                func.count(distinct(ClickLog.user_id)).label("unique_users"),
            )
            .join(ClickLog, Tool.id == ClickLog.tool_id)
            .where(ClickLog.clicked_at >= start_date)
            .group_by(Tool.id, Tool.name)
            .order_by(func.count(ClickLog.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "tool_id": row.id,
                "tool_name": row.name,
                "click_count": row.click_count,
                "unique_users": row.unique_users,
            }
            for row in rows
        ]

    async def get_user_stats(self, days: int = 7, limit: int = 20) -> list[dict]:
        """获取用户活跃排行"""
        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(
                User.id,
                User.name,
                User.avatar_url,
                func.count(ClickLog.id).label("click_count"),
                func.max(ClickLog.clicked_at).label("last_click"),
            )
            .join(ClickLog, User.id == ClickLog.user_id)
            .where(ClickLog.clicked_at >= start_date)
            .group_by(User.id, User.name, User.avatar_url)
            .order_by(func.count(ClickLog.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        def format_last_click(last_click):
            if not last_click:
                return None
            # SQLite 返回字符串，PostgreSQL 返回 datetime 对象
            if isinstance(last_click, str):
                return last_click[:16]  # "2024-01-01 12:00:00" -> "2024-01-01 12:00"
            return last_click.strftime("%Y-%m-%d %H:%M")

        return [
            {
                "user_id": row.id,
                "user_name": row.name,
                "avatar_url": row.avatar_url,
                "click_count": row.click_count,
                "last_click": format_last_click(row.last_click),
            }
            for row in rows
        ]

    async def get_trend(self, days: int = 30) -> list[dict]:
        """获取使用趋势"""
        start_date = datetime.now() - timedelta(days=days)

        query = (
            select(
                func.date(ClickLog.clicked_at).label("date"),
                func.count(ClickLog.id).label("pv"),
                func.count(distinct(ClickLog.user_id)).label("uv"),
            )
            .where(ClickLog.clicked_at >= start_date)
            .group_by(func.date(ClickLog.clicked_at))
            .order_by(func.date(ClickLog.clicked_at))
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                # SQLite 返回字符串，PostgreSQL 返回 date 对象
                "date": row.date if isinstance(row.date, str) else row.date.isoformat(),
                "pv": row.pv,
                "uv": row.uv,
            }
            for row in rows
        ]

    async def generate_daily_report(self) -> dict:
        """生成日报数据"""
        overview = await self.get_overview()
        tool_stats = await self.get_tool_stats(days=1, limit=5)

        return {
            "date": date.today().isoformat(),
            "overview": overview,
            "top_tools": tool_stats,
        }
