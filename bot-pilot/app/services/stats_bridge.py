"""
统计服务桥接层
复用现有后端的统计能力，并扩展新功能
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from loguru import logger
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import async_session


class StatsBridge:
    """
    统计服务桥接器
    提供给 MCP Tools 使用的数据查询接口
    """

    async def get_overview(self) -> dict[str, Any]:
        """
        获取今日数据概览
        """
        async with async_session() as session:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            # 今日 PV
            today_pv = await self._get_pv(session, today, today)
            yesterday_pv = await self._get_pv(session, yesterday, yesterday)

            # 今日 UV
            today_uv = await self._get_uv(session, today, today)
            yesterday_uv = await self._get_uv(session, yesterday, yesterday)

            # 新增用户
            new_users = await self._get_new_users(session, today)

            # 工具总数
            tool_count = await self._get_tool_count(session)

            # 活跃工具数 (今日有点击)
            active_tools = await self._get_active_tools(session, today)

            # 计算环比
            pv_change = self._calc_change(today_pv, yesterday_pv)
            uv_change = self._calc_change(today_uv, yesterday_uv)

            return {
                "date": str(today),
                "pv": today_pv,
                "pv_change": pv_change,
                "uv": today_uv,
                "uv_change": uv_change,
                "new_users": new_users,
                "tool_count": tool_count,
                "active_tools": active_tools,
            }

    async def get_tool_ranking(self, days: int = 7, limit: int = 10) -> dict[str, Any]:
        """
        获取工具排行榜
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.icon_url,
                    COUNT(*) as click_count,
                    COUNT(DISTINCT c.user_id) as user_count
                FROM tools t
                JOIN click_logs c ON t.id = c.tool_id
                WHERE DATE(c.clicked_at) >= :start_date
                GROUP BY t.id, t.name, t.icon_url
                ORDER BY click_count DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            tools = [
                {
                    "rank": i + 1,
                    "id": row[0],
                    "name": row[1],
                    "icon_url": row[2],
                    "click_count": row[3],
                    "user_count": row[4],
                }
                for i, row in enumerate(rows)
            ]

            return {
                "period": f"近{days}天",
                "tools": tools,
                "total": len(tools),
            }

    async def get_user_ranking(self, days: int = 7, limit: int = 10) -> dict[str, Any]:
        """
        获取用户活跃排行榜
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    u.id,
                    u.name,
                    u.avatar_url,
                    COUNT(*) as click_count,
                    MAX(c.clicked_at) as last_active
                FROM users u
                JOIN click_logs c ON u.id = c.user_id
                WHERE DATE(c.clicked_at) >= :start_date
                GROUP BY u.id, u.name, u.avatar_url
                ORDER BY click_count DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            users = [
                {
                    "rank": i + 1,
                    "id": row[0],
                    "name": row[1] or "未知用户",
                    "avatar_url": row[2],
                    "click_count": row[3],
                    "last_active": str(row[4]) if row[4] else None,
                }
                for i, row in enumerate(rows)
            ]

            return {
                "period": f"近{days}天",
                "users": users,
                "total": len(users),
            }

    async def get_trend(self, days: int = 30) -> dict[str, Any]:
        """
        获取访问趋势
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    DATE(clicked_at) as date,
                    COUNT(*) as pv,
                    COUNT(DISTINCT user_id) as uv
                FROM click_logs
                WHERE DATE(clicked_at) >= :start_date
                GROUP BY DATE(clicked_at)
                ORDER BY date
            """)

            result = await session.execute(query, {"start_date": start_date})
            rows = result.fetchall()

            data = [
                {
                    "date": str(row[0]),
                    "pv": row[1],
                    "uv": row[2],
                }
                for row in rows
            ]

            return {
                "period": f"近{days}天",
                "data": data,
            }

    async def get_tool_detail(self, tool_name: str) -> dict[str, Any]:
        """
        获取工具详情
        """
        async with async_session() as session:
            # 模糊搜索工具
            query = text("""
                SELECT id, name, description, icon_url, target_url, provider
                FROM tools
                WHERE name LIKE :name
                LIMIT 1
            """)

            result = await session.execute(query, {"name": f"%{tool_name}%"})
            tool = result.fetchone()

            if not tool:
                return {"error": f"未找到工具: {tool_name}"}

            tool_id = tool[0]

            # 获取统计数据
            stats_query = text("""
                SELECT
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as total_users
                FROM click_logs
                WHERE tool_id = :tool_id
            """)

            stats_result = await session.execute(stats_query, {"tool_id": tool_id})
            stats = stats_result.fetchone()

            # 获取收藏和点赞数
            interaction_query = text("""
                SELECT
                    (SELECT COUNT(*) FROM user_favorites WHERE tool_id = :tool_id) as favorites,
                    (SELECT COUNT(*) FROM user_likes WHERE tool_id = :tool_id) as likes
            """)

            interaction_result = await session.execute(
                interaction_query, {"tool_id": tool_id}
            )
            interactions = interaction_result.fetchone()

            return {
                "id": tool[0],
                "name": tool[1],
                "description": tool[2],
                "icon_url": tool[3],
                "target_url": tool[4],
                "provider": tool[5],
                "total_clicks": stats[0] if stats else 0,
                "total_users": stats[1] if stats else 0,
                "favorites": interactions[0] if interactions else 0,
                "likes": interactions[1] if interactions else 0,
            }

    async def get_feedback_summary(
        self, days: int = 30, limit: int = 20
    ) -> dict[str, Any]:
        """
        获取反馈汇总
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    id,
                    feedback_type,
                    tool_name,
                    content,
                    created_at
                FROM tool_feedback
                WHERE DATE(created_at) >= :start_date
                ORDER BY created_at DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            feedbacks = [
                {
                    "id": row[0],
                    "type": row[1],
                    "tool_name": row[2],
                    "content": row[3],
                    "created_at": str(row[4]),
                }
                for row in rows
            ]

            # 按类型统计
            type_stats_query = text("""
                SELECT feedback_type, COUNT(*) as count
                FROM tool_feedback
                WHERE DATE(created_at) >= :start_date
                GROUP BY feedback_type
            """)

            type_result = await session.execute(
                type_stats_query, {"start_date": start_date}
            )
            type_stats = {row[0]: row[1] for row in type_result.fetchall()}

            return {
                "period": f"近{days}天",
                "feedbacks": feedbacks,
                "type_stats": type_stats,
                "total": len(feedbacks),
            }

    async def search_tools(
        self, keyword: str, category: Optional[str] = None
    ) -> dict[str, Any]:
        """
        搜索工具
        """
        async with async_session() as session:
            if category:
                query = text("""
                    SELECT t.id, t.name, t.description, t.icon_url, c.name as category
                    FROM tools t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE (t.name LIKE :keyword OR t.description LIKE :keyword)
                    AND c.name LIKE :category
                    LIMIT 20
                """)
                params = {"keyword": f"%{keyword}%", "category": f"%{category}%"}
            else:
                query = text("""
                    SELECT t.id, t.name, t.description, t.icon_url, c.name as category
                    FROM tools t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.name LIKE :keyword OR t.description LIKE :keyword
                    LIMIT 20
                """)
                params = {"keyword": f"%{keyword}%"}

            result = await session.execute(query, params)
            rows = result.fetchall()

            tools = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "icon_url": row[3],
                    "category": row[4],
                }
                for row in rows
            ]

            return {
                "keyword": keyword,
                "category": category,
                "tools": tools,
                "total": len(tools),
            }

    async def get_category_stats(self, days: int = 7) -> dict[str, Any]:
        """
        获取分类统计
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    c.name as category,
                    COUNT(*) as click_count,
                    COUNT(DISTINCT cl.user_id) as user_count
                FROM categories c
                JOIN tools t ON c.id = t.category_id
                JOIN click_logs cl ON t.id = cl.tool_id
                WHERE DATE(cl.clicked_at) >= :start_date
                GROUP BY c.id, c.name
                ORDER BY click_count DESC
            """)

            result = await session.execute(query, {"start_date": start_date})
            rows = result.fetchall()

            categories = [
                {
                    "name": row[0],
                    "click_count": row[1],
                    "user_count": row[2],
                }
                for row in rows
            ]

            return {
                "period": f"近{days}天",
                "categories": categories,
            }

    async def get_retention_stats(self, period: str = "day") -> dict[str, Any]:
        """
        获取用户留存分析
        """
        async with async_session() as session:
            today = datetime.now().date()

            if period == "day":
                # 日留存：昨天访问，今天也访问的用户比例
                yesterday = today - timedelta(days=1)

                query = text("""
                    WITH yesterday_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) = :yesterday
                    ),
                    today_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) = :today
                    )
                    SELECT
                        (SELECT COUNT(*) FROM yesterday_users) as yesterday_count,
                        (SELECT COUNT(*) FROM yesterday_users WHERE user_id IN (SELECT user_id FROM today_users)) as retained_count
                """)

                result = await session.execute(
                    query, {"yesterday": yesterday, "today": today}
                )
                row = result.fetchone()

                yesterday_count = row[0] or 0
                retained_count = row[1] or 0
                retention_rate = (
                    round(retained_count / yesterday_count * 100, 2)
                    if yesterday_count > 0
                    else 0
                )

                return {
                    "period": "日留存",
                    "base_date": str(yesterday),
                    "base_users": yesterday_count,
                    "retained_users": retained_count,
                    "retention_rate": retention_rate,
                }

            elif period == "week":
                # 周留存
                last_week_start = today - timedelta(days=14)
                last_week_end = today - timedelta(days=8)
                this_week_start = today - timedelta(days=7)

                query = text("""
                    WITH last_week_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) BETWEEN :last_week_start AND :last_week_end
                    ),
                    this_week_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) >= :this_week_start
                    )
                    SELECT
                        (SELECT COUNT(*) FROM last_week_users) as last_week_count,
                        (SELECT COUNT(*) FROM last_week_users WHERE user_id IN (SELECT user_id FROM this_week_users)) as retained_count
                """)

                result = await session.execute(
                    query,
                    {
                        "last_week_start": last_week_start,
                        "last_week_end": last_week_end,
                        "this_week_start": this_week_start,
                    },
                )
                row = result.fetchone()

                last_week_count = row[0] or 0
                retained_count = row[1] or 0
                retention_rate = (
                    round(retained_count / last_week_count * 100, 2)
                    if last_week_count > 0
                    else 0
                )

                return {
                    "period": "周留存",
                    "base_period": f"{last_week_start} ~ {last_week_end}",
                    "base_users": last_week_count,
                    "retained_users": retained_count,
                    "retention_rate": retention_rate,
                }

            else:  # month
                # 月留存
                last_month_start = today - timedelta(days=60)
                last_month_end = today - timedelta(days=31)
                this_month_start = today - timedelta(days=30)

                query = text("""
                    WITH last_month_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) BETWEEN :last_month_start AND :last_month_end
                    ),
                    this_month_users AS (
                        SELECT DISTINCT user_id
                        FROM click_logs
                        WHERE DATE(clicked_at) >= :this_month_start
                    )
                    SELECT
                        (SELECT COUNT(*) FROM last_month_users) as last_month_count,
                        (SELECT COUNT(*) FROM last_month_users WHERE user_id IN (SELECT user_id FROM this_month_users)) as retained_count
                """)

                result = await session.execute(
                    query,
                    {
                        "last_month_start": last_month_start,
                        "last_month_end": last_month_end,
                        "this_month_start": this_month_start,
                    },
                )
                row = result.fetchone()

                last_month_count = row[0] or 0
                retained_count = row[1] or 0
                retention_rate = (
                    round(retained_count / last_month_count * 100, 2)
                    if last_month_count > 0
                    else 0
                )

                return {
                    "period": "月留存",
                    "base_period": f"{last_month_start} ~ {last_month_end}",
                    "base_users": last_month_count,
                    "retained_users": retained_count,
                    "retention_rate": retention_rate,
                }

    async def get_hourly_distribution(self, days: int = 7) -> dict[str, Any]:
        """
        获取按小时的访问分布
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            # SQLite 和 PostgreSQL 的小时提取语法不同
            from app.config import settings

            if settings.is_sqlite:
                hour_expr = "strftime('%H', clicked_at)"
            else:
                hour_expr = "EXTRACT(HOUR FROM clicked_at)"

            query = text(f"""
                SELECT
                    {hour_expr} as hour,
                    COUNT(*) as click_count
                FROM click_logs
                WHERE DATE(clicked_at) >= :start_date
                GROUP BY hour
                ORDER BY hour
            """)

            result = await session.execute(query, {"start_date": start_date})
            rows = result.fetchall()

            # 构建 24 小时分布
            distribution = {str(i).zfill(2): 0 for i in range(24)}
            for row in rows:
                hour = str(int(row[0])).zfill(2)
                distribution[hour] = row[1]

            # 找出高峰时段
            peak_hour = max(distribution, key=distribution.get)
            peak_count = distribution[peak_hour]

            return {
                "period": f"近{days}天",
                "distribution": distribution,
                "peak_hour": f"{peak_hour}:00",
                "peak_count": peak_count,
            }

    # ========== 辅助方法 ==========

    async def _get_pv(
        self, session: AsyncSession, start_date, end_date
    ) -> int:
        """获取 PV"""
        query = text("""
            SELECT COUNT(*) FROM click_logs
            WHERE DATE(clicked_at) BETWEEN :start_date AND :end_date
        """)
        result = await session.execute(
            query, {"start_date": start_date, "end_date": end_date}
        )
        return result.scalar() or 0

    async def _get_uv(
        self, session: AsyncSession, start_date, end_date
    ) -> int:
        """获取 UV"""
        query = text("""
            SELECT COUNT(DISTINCT user_id) FROM click_logs
            WHERE DATE(clicked_at) BETWEEN :start_date AND :end_date
        """)
        result = await session.execute(
            query, {"start_date": start_date, "end_date": end_date}
        )
        return result.scalar() or 0

    async def _get_new_users(self, session: AsyncSession, date) -> int:
        """获取新增用户数"""
        query = text("""
            SELECT COUNT(*) FROM users
            WHERE DATE(first_visit_at) = :date
        """)
        result = await session.execute(query, {"date": date})
        return result.scalar() or 0

    async def _get_tool_count(self, session: AsyncSession) -> int:
        """获取工具总数"""
        query = text("SELECT COUNT(*) FROM tools WHERE is_active = 1")
        result = await session.execute(query)
        return result.scalar() or 0

    async def _get_active_tools(self, session: AsyncSession, date) -> int:
        """获取活跃工具数"""
        query = text("""
            SELECT COUNT(DISTINCT tool_id) FROM click_logs
            WHERE DATE(clicked_at) = :date
        """)
        result = await session.execute(query, {"date": date})
        return result.scalar() or 0

    def _calc_change(self, current: int, previous: int) -> float:
        """计算环比变化百分比"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round((current - previous) / previous * 100, 2)

    # ========== 新增工具方法 ==========

    async def get_provider_stats(self, days: int = 7, limit: int = 10) -> dict[str, Any]:
        """
        获取提供者统计（谁推荐的工具最多/最受欢迎）
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    t.provider,
                    COUNT(DISTINCT t.id) as tool_count,
                    COUNT(c.id) as total_clicks,
                    COUNT(DISTINCT c.user_id) as user_count
                FROM tools t
                LEFT JOIN click_logs c ON t.id = c.tool_id
                    AND DATE(c.clicked_at) >= :start_date
                WHERE t.provider IS NOT NULL AND t.provider != ''
                GROUP BY t.provider
                ORDER BY total_clicks DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            providers = [
                {
                    "rank": i + 1,
                    "name": row[0],
                    "tool_count": row[1],
                    "total_clicks": row[2],
                    "user_count": row[3],
                }
                for i, row in enumerate(rows)
            ]

            return {
                "period": f"近{days}天",
                "providers": providers,
                "total": len(providers),
            }

    async def get_tool_interactions(self, limit: int = 10) -> dict[str, Any]:
        """
        获取工具互动排行（收藏+点赞）
        """
        async with async_session() as session:
            query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.icon_url,
                    COALESCE(f.fav_count, 0) as favorites,
                    COALESCE(l.like_count, 0) as likes,
                    COALESCE(f.fav_count, 0) + COALESCE(l.like_count, 0) as score
                FROM tools t
                LEFT JOIN (
                    SELECT tool_id, COUNT(*) as fav_count
                    FROM user_favorites
                    GROUP BY tool_id
                ) f ON t.id = f.tool_id
                LEFT JOIN (
                    SELECT tool_id, COUNT(*) as like_count
                    FROM user_likes
                    GROUP BY tool_id
                ) l ON t.id = l.tool_id
                WHERE t.is_active = 1
                ORDER BY score DESC
                LIMIT :limit
            """)

            result = await session.execute(query, {"limit": limit})
            rows = result.fetchall()

            tools = [
                {
                    "rank": i + 1,
                    "id": row[0],
                    "name": row[1],
                    "icon_url": row[2],
                    "favorites": row[3],
                    "likes": row[4],
                    "score": row[5],
                }
                for i, row in enumerate(rows)
            ]

            return {
                "tools": tools,
                "total": len(tools),
            }

    async def get_hot_tools(self, days: int = 7, limit: int = 10) -> dict[str, Any]:
        """
        获取热门新工具（最近新增且点击量高）
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.description,
                    t.icon_url,
                    t.created_at,
                    COUNT(c.id) as click_count
                FROM tools t
                LEFT JOIN click_logs c ON t.id = c.tool_id
                WHERE t.is_active = 1
                    AND DATE(t.created_at) >= :start_date
                GROUP BY t.id, t.name, t.description, t.icon_url, t.created_at
                ORDER BY click_count DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            # 判断是否热门（点击量 > 10 为热门）
            tools = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2][:100] if row[2] else None,
                    "icon_url": row[3],
                    "created_at": str(row[4])[:10] if row[4] else None,
                    "click_count": row[5],
                    "is_hot": row[5] > 10,
                }
                for row in rows
            ]

            return {
                "period": f"近{days}天新增",
                "tools": tools,
                "total": len(tools),
            }

    async def get_want_list(self, days: int = 30, limit: int = 20) -> dict[str, Any]:
        """
        获取用户想要的工具列表
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            query = text("""
                SELECT
                    tool_name,
                    COUNT(*) as count,
                    MAX(created_at) as latest_at
                FROM tool_feedback
                WHERE feedback_type = 'want'
                    AND DATE(created_at) >= :start_date
                    AND tool_name IS NOT NULL AND tool_name != ''
                GROUP BY tool_name
                ORDER BY count DESC, latest_at DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            wants = [
                {
                    "tool_name": row[0],
                    "count": row[1],
                    "latest_at": str(row[2])[:10] if row[2] else None,
                }
                for row in rows
            ]

            return {
                "period": f"近{days}天",
                "wants": wants,
                "total": len(wants),
            }

    async def get_search_keywords(self, days: int = 7, limit: int = 20) -> dict[str, Any]:
        """
        获取搜索热词
        """
        async with async_session() as session:
            start_date = datetime.now().date() - timedelta(days=days)

            # 聚合搜索关键词
            query = text("""
                SELECT
                    keyword,
                    COUNT(*) as count
                FROM search_history
                WHERE DATE(searched_at) >= :start_date
                    AND keyword IS NOT NULL AND keyword != ''
                GROUP BY keyword
                ORDER BY count DESC
                LIMIT :limit
            """)

            result = await session.execute(
                query, {"start_date": start_date, "limit": limit}
            )
            rows = result.fetchall()

            keywords = []
            for row in rows:
                keyword = row[0]
                count = row[1]

                # 检查是否有匹配的工具
                check_query = text("""
                    SELECT COUNT(*) FROM tools
                    WHERE is_active = 1
                        AND (name LIKE :kw OR description LIKE :kw)
                """)
                check_result = await session.execute(
                    check_query, {"kw": f"%{keyword}%"}
                )
                has_result = (check_result.scalar() or 0) > 0

                keywords.append({
                    "keyword": keyword,
                    "count": count,
                    "has_result": has_result,
                })

            return {
                "period": f"近{days}天",
                "keywords": keywords,
                "total": len(keywords),
            }

    async def recommend_by_scenario(
        self, scenario: str, limit: int = 5
    ) -> dict[str, Any]:
        """
        根据场景推荐工具
        """
        async with async_session() as session:
            # 先从分类名称匹配
            category_query = text("""
                SELECT
                    t.id,
                    t.name,
                    t.description,
                    t.icon_url,
                    c.name as category,
                    COUNT(cl.id) as click_count
                FROM tools t
                JOIN categories c ON t.category_id = c.id
                LEFT JOIN click_logs cl ON t.id = cl.tool_id
                WHERE t.is_active = 1
                    AND (c.name LIKE :scenario
                         OR t.name LIKE :scenario
                         OR t.description LIKE :scenario)
                GROUP BY t.id, t.name, t.description, t.icon_url, c.name
                ORDER BY click_count DESC
                LIMIT :limit
            """)

            result = await session.execute(
                category_query,
                {"scenario": f"%{scenario}%", "limit": limit}
            )
            rows = result.fetchall()

            recommended = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2][:100] if row[2] else None,
                    "icon_url": row[3],
                    "category": row[4],
                    "click_count": row[5],
                    "reason": f"属于「{row[4]}」分类，点击量 {row[5]}",
                }
                for row in rows
            ]

            return {
                "scenario": scenario,
                "recommended": recommended,
                "total": len(recommended),
            }
