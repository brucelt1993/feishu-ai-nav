"""
飞书卡片消息构建器
生成精美的数据可视化卡片
"""

from typing import Any


class CardBuilder:
    """卡片构建器"""

    # 主题色
    THEME_COLOR = "#1677FF"  # 蓝色
    SUCCESS_COLOR = "#52C41A"  # 绿色
    WARNING_COLOR = "#FAAD14"  # 黄色
    ERROR_COLOR = "#FF4D4F"  # 红色

    @classmethod
    def build_overview_card(cls, data: dict[str, Any]) -> dict:
        """
        构建数据概览卡片

        Args:
            data: 概览数据 (来自 get_overview)

        Returns:
            飞书卡片 JSON
        """
        pv_change = data.get("pv_change", 0)
        uv_change = data.get("uv_change", 0)

        pv_arrow = "📈" if pv_change >= 0 else "📉"
        uv_arrow = "📈" if uv_change >= 0 else "📉"

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "📊 今日数据概览", "tag": "plain_text"},
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**访问量 (PV)**\n{data.get('pv', 0):,} {pv_arrow} {abs(pv_change):.1f}%",
                            },
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**独立用户 (UV)**\n{data.get('uv', 0):,} {uv_arrow} {abs(uv_change):.1f}%",
                            },
                        },
                    ],
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**新增用户**\n👤 {data.get('new_users', 0)}",
                            },
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**活跃工具**\n🔧 {data.get('active_tools', 0)} / {data.get('tool_count', 0)}",
                            },
                        },
                    ],
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"📅 统计日期: {data.get('date', '今日')}",
                        }
                    ],
                },
            ],
        }

    @classmethod
    def build_tool_ranking_card(
        cls, data: dict[str, Any], title: str = "🏆 热门工具排行"
    ) -> dict:
        """
        构建工具排行卡片

        Args:
            data: 排行数据 (来自 get_tool_ranking)
            title: 卡片标题

        Returns:
            飞书卡片 JSON
        """
        tools = data.get("tools", [])

        # 构建排行列表
        ranking_items = []
        for tool in tools[:10]:
            rank = tool.get("rank", 0)
            name = tool.get("name", "未知")
            clicks = tool.get("click_count", 0)

            # 排名图标
            if rank == 1:
                rank_icon = "🥇"
            elif rank == 2:
                rank_icon = "🥈"
            elif rank == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"{rank}."

            ranking_items.append(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"{rank_icon} **{name}**　🔥 {clicks:,} 次",
                    },
                }
            )

        elements = [
            *ranking_items,
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"📅 统计周期: {data.get('period', '近7天')}",
                    }
                ],
            },
        ]

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "orange",
                "title": {"content": title, "tag": "plain_text"},
            },
            "elements": elements,
        }

    @classmethod
    def build_user_ranking_card(
        cls, data: dict[str, Any], title: str = "👑 活跃用户排行"
    ) -> dict:
        """
        构建用户排行卡片

        Args:
            data: 排行数据 (来自 get_user_ranking)
            title: 卡片标题

        Returns:
            飞书卡片 JSON
        """
        users = data.get("users", [])

        # 构建排行列表
        ranking_items = []
        for user in users[:10]:
            rank = user.get("rank", 0)
            name = user.get("name", "未知用户")
            clicks = user.get("click_count", 0)
            last_active = user.get("last_active", "")

            # 排名图标
            if rank == 1:
                rank_icon = "🥇"
            elif rank == 2:
                rank_icon = "🥈"
            elif rank == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"{rank}."

            # 简化最后活跃时间
            active_text = ""
            if last_active:
                active_text = f"　⏰ {last_active[:10]}"

            ranking_items.append(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"{rank_icon} **{name}**　💎 {clicks:,} 次{active_text}",
                    },
                }
            )

        elements = [
            *ranking_items,
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"📅 统计周期: {data.get('period', '近7天')}",
                    }
                ],
            },
        ]

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "purple",
                "title": {"content": title, "tag": "plain_text"},
            },
            "elements": elements,
        }

    @classmethod
    def build_tool_search_card(cls, data: dict[str, Any]) -> dict:
        """
        构建工具搜索结果卡片

        Args:
            data: 搜索结果 (来自 search_tools)

        Returns:
            飞书卡片 JSON
        """
        tools = data.get("tools", [])
        keyword = data.get("keyword", "")

        elements = []

        if not tools:
            elements.append(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"😕 未找到与 **{keyword}** 相关的工具",
                    },
                }
            )
        else:
            for tool in tools[:5]:
                name = tool.get("name", "")
                desc = tool.get("description", "暂无描述")
                category = tool.get("category", "")

                elements.append(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"🔧 **{name}**\n{desc[:50]}...\n📁 {category}",
                        },
                    }
                )
                elements.append({"tag": "hr"})

        # 移除最后一个分隔线
        if elements and elements[-1].get("tag") == "hr":
            elements.pop()

        elements.append(
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"🔍 搜索关键词: {keyword} | 共 {len(tools)} 个结果",
                    }
                ],
            }
        )

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {"content": "🔍 工具搜索结果", "tag": "plain_text"},
            },
            "elements": elements,
        }

    @classmethod
    def build_retention_card(cls, data: dict[str, Any]) -> dict:
        """
        构建留存分析卡片

        Args:
            data: 留存数据 (来自 get_retention_stats)

        Returns:
            飞书卡片 JSON
        """
        period = data.get("period", "")
        base_users = data.get("base_users", 0)
        retained_users = data.get("retained_users", 0)
        retention_rate = data.get("retention_rate", 0)

        # 留存率颜色
        if retention_rate >= 50:
            rate_color = "green"
        elif retention_rate >= 30:
            rate_color = "yellow"
        else:
            rate_color = "red"

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "turquoise",
                "title": {"content": f"📊 {period}分析", "tag": "plain_text"},
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**基准用户数**\n👥 {base_users:,}",
                            },
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**留存用户数**\n✅ {retained_users:,}",
                            },
                        },
                    ],
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**留存率**: {retention_rate}%",
                    },
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"📅 基准时段: {data.get('base_period', data.get('base_date', ''))}",
                        }
                    ],
                },
            ],
        }

    @classmethod
    def build_hourly_distribution_card(cls, data: dict[str, Any]) -> dict:
        """
        构建时段分布卡片

        Args:
            data: 时段数据 (来自 get_hourly_distribution)

        Returns:
            飞书卡片 JSON
        """
        distribution = data.get("distribution", {})
        peak_hour = data.get("peak_hour", "")
        peak_count = data.get("peak_count", 0)

        # 构建简化的时段展示 (每3小时一组)
        time_groups = []
        for start in range(0, 24, 3):
            end = start + 3
            total = sum(
                distribution.get(str(h).zfill(2), 0) for h in range(start, end)
            )
            time_groups.append(f"{start:02d}-{end:02d}时: {total:,}")

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "indigo",
                "title": {"content": "⏰ 访问时段分布", "tag": "plain_text"},
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"🔥 **高峰时段**: {peak_hour}，访问量 {peak_count:,}",
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "\n".join(time_groups),
                    },
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"📅 统计周期: {data.get('period', '近7天')}",
                        }
                    ],
                },
            ],
        }

    @classmethod
    def build_error_card(cls, error: str) -> dict:
        """
        构建错误提示卡片

        Args:
            error: 错误信息

        Returns:
            飞书卡片 JSON
        """
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "red",
                "title": {"content": "⚠️ 出错了", "tag": "plain_text"},
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"处理请求时遇到问题：\n\n{error[:200]}",
                    },
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "请稍后重试，或联系管理员",
                        }
                    ],
                },
            ],
        }
