"""统计服务"""
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Tool, User, ClickLog, UserFavorite, UserLike, ToolFeedback
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
            "total_pv": total_pv,      # 总PV
            "total_uv": total_uv,      # 总UV
            "total_tools": total_tools,
            "new_users_today": new_users_today,
        }

    async def get_extended_overview(self) -> dict:
        """获取扩展的统计概览（含互动数据和环比）"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        today_start = datetime.combine(today, datetime.min.time())
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        week_start = datetime.now() - timedelta(days=7)

        # 今日PV
        today_pv = await self._count_clicks(today_start)
        yesterday_pv = await self._count_clicks(yesterday_start, today_start)

        # 今日UV
        today_uv = await self._count_unique_users(today_start)
        yesterday_uv = await self._count_unique_users(yesterday_start, today_start)

        # 总PV
        total_pv = await self._count_clicks()

        # 总UV（有点击记录的用户数）
        total_uv_query = select(func.count(User.id))
        total_uv = (await self.db.execute(total_uv_query)).scalar() or 0

        # 工具总数
        tools_query = select(func.count(Tool.id)).where(Tool.is_active == True)
        total_tools = (await self.db.execute(tools_query)).scalar() or 0

        # 今日新增用户
        new_users_today = await self._count_new_users(today_start)
        new_users_yesterday = await self._count_new_users(yesterday_start, today_start)

        # 7日活跃用户（有点击记录的用户）
        active_users_7d_query = select(func.count(distinct(ClickLog.user_id))).where(
            ClickLog.clicked_at >= week_start
        )
        active_users_7d = (await self.db.execute(active_users_7d_query)).scalar() or 0

        # 总收藏数
        total_favorites_query = select(func.count(UserFavorite.id))
        total_favorites = (await self.db.execute(total_favorites_query)).scalar() or 0

        # 总点赞数
        total_likes_query = select(func.count(UserLike.id))
        total_likes = (await self.db.execute(total_likes_query)).scalar() or 0

        return {
            "today_pv": today_pv,
            "today_pv_trend": self._calc_trend(today_pv, yesterday_pv),
            "today_uv": today_uv,
            "today_uv_trend": self._calc_trend(today_uv, yesterday_uv),
            "total_pv": total_pv,
            "total_uv": total_uv,
            "new_users_today": new_users_today,
            "new_users_trend": self._calc_trend(new_users_today, new_users_yesterday),
            "active_users_7d": active_users_7d,
            "total_favorites": total_favorites,
            "total_likes": total_likes,
            "total_tools": total_tools,
        }

    def _calc_trend(self, current: int, previous: int) -> float:
        """计算环比增长率"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 1)

    async def _count_clicks(self, start: datetime = None, end: datetime = None) -> int:
        """统计点击数"""
        query = select(func.count(ClickLog.id))
        if start:
            query = query.where(ClickLog.clicked_at >= start)
        if end:
            query = query.where(ClickLog.clicked_at < end)
        return (await self.db.execute(query)).scalar() or 0

    async def _count_unique_users(self, start: datetime = None, end: datetime = None) -> int:
        """统计独立用户数"""
        query = select(func.count(distinct(ClickLog.user_id)))
        if start:
            query = query.where(ClickLog.clicked_at >= start)
        if end:
            query = query.where(ClickLog.clicked_at < end)
        return (await self.db.execute(query)).scalar() or 0

    async def _count_new_users(self, start: datetime, end: datetime = None) -> int:
        """统计新增用户数"""
        query = select(func.count(User.id)).where(User.first_visit_at >= start)
        if end:
            query = query.where(User.first_visit_at < end)
        return (await self.db.execute(query)).scalar() or 0

    async def get_tool_stats(self, days: int = 7, limit: int = 10) -> list[dict]:
        """获取工具使用排行（含环比和提供者）"""
        now = datetime.now()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        # 当前周期统计
        current_query = (
            select(
                Tool.id,
                Tool.name,
                Tool.provider,
                func.count(ClickLog.id).label("click_count"),
                func.count(distinct(ClickLog.user_id)).label("unique_users"),
            )
            .join(ClickLog, Tool.id == ClickLog.tool_id)
            .where(ClickLog.clicked_at >= current_start)
            .group_by(Tool.id, Tool.name, Tool.provider)
            .order_by(func.count(ClickLog.id).desc())
            .limit(limit)
        )
        current_result = await self.db.execute(current_query)
        current_rows = current_result.all()

        # 获取这些工具在上周期的数据
        tool_ids = [row.id for row in current_rows]
        previous_stats = {}
        if tool_ids:
            previous_query = (
                select(
                    ClickLog.tool_id,
                    func.count(ClickLog.id).label("click_count"),
                    func.count(distinct(ClickLog.user_id)).label("unique_users"),
                )
                .where(
                    ClickLog.tool_id.in_(tool_ids),
                    ClickLog.clicked_at >= previous_start,
                    ClickLog.clicked_at < current_start
                )
                .group_by(ClickLog.tool_id)
            )
            previous_result = await self.db.execute(previous_query)
            for row in previous_result.all():
                previous_stats[row.tool_id] = {
                    "click_count": row.click_count,
                    "unique_users": row.unique_users,
                }

        return [
            {
                "tool_id": row.id,
                "tool_name": row.name,
                "provider": row.provider or "",
                "click_count": row.click_count,
                "unique_users": row.unique_users,
                "pv_trend": self._calc_trend(
                    row.click_count,
                    previous_stats.get(row.id, {}).get("click_count", 0)
                ),
                "uv_trend": self._calc_trend(
                    row.unique_users,
                    previous_stats.get(row.id, {}).get("unique_users", 0)
                ),
            }
            for row in current_rows
        ]

    async def get_user_stats(self, days: int = 7, limit: int = 20) -> list[dict]:
        """获取用户活跃排行（含环比）"""
        now = datetime.now()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        # 当前周期统计
        current_query = (
            select(
                User.id,
                User.name,
                User.avatar_url,
                func.count(ClickLog.id).label("click_count"),
                func.max(ClickLog.clicked_at).label("last_click"),
            )
            .join(ClickLog, User.id == ClickLog.user_id)
            .where(ClickLog.clicked_at >= current_start)
            .group_by(User.id, User.name, User.avatar_url)
            .order_by(func.count(ClickLog.id).desc())
            .limit(limit)
        )
        current_result = await self.db.execute(current_query)
        current_rows = current_result.all()

        # 获取这些用户在上周期的数据
        user_ids = [row.id for row in current_rows]
        previous_stats = {}
        if user_ids:
            previous_query = (
                select(
                    ClickLog.user_id,
                    func.count(ClickLog.id).label("click_count"),
                )
                .where(
                    ClickLog.user_id.in_(user_ids),
                    ClickLog.clicked_at >= previous_start,
                    ClickLog.clicked_at < current_start
                )
                .group_by(ClickLog.user_id)
            )
            previous_result = await self.db.execute(previous_query)
            for row in previous_result.all():
                previous_stats[row.user_id] = row.click_count

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
                "click_trend": self._calc_trend(
                    row.click_count,
                    previous_stats.get(row.id, 0)
                ),
                "last_click": format_last_click(row.last_click),
            }
            for row in current_rows
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

    async def get_category_distribution(self) -> list[dict]:
        """获取分类使用分布（按一级分类聚合，包含其子分类的工具点击）"""
        from ..models import Category
        from sqlalchemy import or_, case
        from sqlalchemy.orm import aliased

        # 先查出所有一级分类
        parent_cats_query = select(Category).where(Category.parent_id.is_(None))
        parent_cats_result = await self.db.execute(parent_cats_query)
        parent_cats = {cat.id: cat for cat in parent_cats_result.scalars().all()}

        if not parent_cats:
            return []

        # 查询所有分类的点击统计（包括一级和二级）
        cat_alias = aliased(Category)
        query = (
            select(
                Category.id,
                Category.parent_id,
                func.count(ClickLog.id).label("click_count"),
                func.count(distinct(ClickLog.user_id)).label("unique_users"),
            )
            .join(Tool, Category.id == Tool.category_id)
            .join(ClickLog, Tool.id == ClickLog.tool_id)
            .group_by(Category.id, Category.parent_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 按一级分类聚合
        aggregated = {}
        for row in rows:
            # 确定归属的一级分类
            if row.parent_id is None:
                # 本身就是一级分类
                parent_id = row.id
            else:
                # 二级分类，归属到其父分类
                parent_id = row.parent_id

            if parent_id not in aggregated:
                aggregated[parent_id] = {"click_count": 0, "unique_users": 0}

            aggregated[parent_id]["click_count"] += row.click_count
            aggregated[parent_id]["unique_users"] += row.unique_users

        # 构建返回结果
        result_list = []
        for parent_id, stats in aggregated.items():
            if parent_id in parent_cats:
                cat = parent_cats[parent_id]
                result_list.append({
                    "category_id": cat.id,
                    "category_name": cat.name,
                    "color": cat.color or "#667eea",
                    "click_count": stats["click_count"],
                    "unique_users": stats["unique_users"],
                })

        # 按点击数排序
        result_list.sort(key=lambda x: x["click_count"], reverse=True)
        return result_list

    async def get_tool_detail_stats(self, tool_id: int, days: int = 30) -> dict:
        """获取单个工具的详细统计"""
        start_date = datetime.now() - timedelta(days=days)

        # 基础统计
        base_query = select(
            func.count(ClickLog.id).label("pv"),
            func.count(distinct(ClickLog.user_id)).label("uv"),
        ).where(
            ClickLog.tool_id == tool_id,
            ClickLog.clicked_at >= start_date
        )
        base_result = await self.db.execute(base_query)
        base_row = base_result.one()

        # 日趋势
        trend_query = (
            select(
                func.date(ClickLog.clicked_at).label("date"),
                func.count(ClickLog.id).label("pv"),
                func.count(distinct(ClickLog.user_id)).label("uv"),
            )
            .where(
                ClickLog.tool_id == tool_id,
                ClickLog.clicked_at >= start_date
            )
            .group_by(func.date(ClickLog.clicked_at))
            .order_by(func.date(ClickLog.clicked_at))
        )
        trend_result = await self.db.execute(trend_query)
        trend_rows = trend_result.all()

        return {
            "tool_id": tool_id,
            "total_pv": base_row.pv or 0,
            "total_uv": base_row.uv or 0,
            "trend": [
                {
                    "date": row.date if isinstance(row.date, str) else row.date.isoformat(),
                    "pv": row.pv,
                    "uv": row.uv,
                }
                for row in trend_rows
            ]
        }

    async def generate_daily_report(self) -> dict:
        """生成日报数据"""
        overview = await self.get_overview()
        tool_stats = await self.get_tool_stats(days=1, limit=5)

        return {
            "date": date.today().isoformat(),
            "overview": overview,
            "top_tools": tool_stats,
        }

    async def get_tool_interactions(self, limit: int = 20) -> list[dict]:
        """获取工具点赞收藏统计"""
        # 统计每个工具的收藏数和点赞数
        favorites_subq = (
            select(
                UserFavorite.tool_id,
                func.count(UserFavorite.id).label("favorite_count")
            )
            .group_by(UserFavorite.tool_id)
            .subquery()
        )

        likes_subq = (
            select(
                UserLike.tool_id,
                func.count(UserLike.id).label("like_count")
            )
            .group_by(UserLike.tool_id)
            .subquery()
        )

        query = (
            select(
                Tool.id,
                Tool.name,
                Tool.provider,
                func.coalesce(favorites_subq.c.favorite_count, 0).label("favorite_count"),
                func.coalesce(likes_subq.c.like_count, 0).label("like_count"),
            )
            .outerjoin(favorites_subq, Tool.id == favorites_subq.c.tool_id)
            .outerjoin(likes_subq, Tool.id == likes_subq.c.tool_id)
            .where(Tool.is_active == True)
            .order_by(
                (func.coalesce(favorites_subq.c.favorite_count, 0) +
                 func.coalesce(likes_subq.c.like_count, 0)).desc()
            )
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "tool_id": row.id,
                "tool_name": row.name,
                "provider": row.provider or "",
                "favorite_count": row.favorite_count,
                "like_count": row.like_count,
                "total": row.favorite_count + row.like_count,
            }
            for row in rows
        ]

    async def get_provider_stats(self, limit: int = 20) -> list[dict]:
        """获取提供者统计（按provider分组统计工具数和点击数）"""
        # 统计每个provider提供的工具数
        tool_count_subq = (
            select(
                Tool.provider,
                func.count(Tool.id).label("tool_count")
            )
            .where(Tool.is_active == True, Tool.provider.isnot(None), Tool.provider != "")
            .group_by(Tool.provider)
            .subquery()
        )

        # 统计每个provider工具的总点击数
        click_count_subq = (
            select(
                Tool.provider,
                func.count(ClickLog.id).label("click_count")
            )
            .join(ClickLog, Tool.id == ClickLog.tool_id)
            .where(Tool.provider.isnot(None), Tool.provider != "")
            .group_by(Tool.provider)
            .subquery()
        )

        query = (
            select(
                tool_count_subq.c.provider,
                tool_count_subq.c.tool_count,
                func.coalesce(click_count_subq.c.click_count, 0).label("click_count"),
            )
            .outerjoin(click_count_subq, tool_count_subq.c.provider == click_count_subq.c.provider)
            .order_by(tool_count_subq.c.tool_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "provider": row.provider,
                "tool_count": row.tool_count,
                "click_count": row.click_count,
            }
            for row in rows
        ]

    async def get_want_list(self, limit: int = 50) -> list[dict]:
        """获取用户想要的工具列表（按工具名称聚合统计想要次数）"""
        query = (
            select(
                ToolFeedback.tool_name,
                func.count(ToolFeedback.id).label("want_count"),
            )
            .where(ToolFeedback.feedback_type == "want")
            .where(ToolFeedback.tool_name.isnot(None))
            .where(ToolFeedback.tool_name != "")
            .group_by(ToolFeedback.tool_name)
            .order_by(func.count(ToolFeedback.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "tool_name": row.tool_name,
                "want_count": row.want_count,
            }
            for row in rows
        ]
