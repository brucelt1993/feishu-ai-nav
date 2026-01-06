"""
MCP Tools 定义
基于 OpenAI Function Calling 实现
"""

from typing import Any

# MCP 工具定义 (OpenAI Function Calling 格式)
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_overview",
            "description": "获取 AI 导航平台今日数据概览，包括 PV、UV、新增用户、工具数等基础指标",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tool_ranking",
            "description": "获取工具排行榜，按点击量排序",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_ranking",
            "description": "获取用户活跃排行榜，按点击量排序",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend",
            "description": "获取访问趋势数据，返回每日 PV/UV",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认30天",
                        "default": 30,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tool_detail",
            "description": "获取单个工具的详细统计信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "工具名称（模糊匹配）",
                    },
                },
                "required": ["tool_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_feedback_summary",
            "description": "获取用户反馈汇总，包括想要的工具、建议、问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认30天",
                        "default": 30,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认20",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tools",
            "description": "搜索 AI 工具，支持按名称、分类、关键词搜索",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词",
                    },
                    "category": {
                        "type": "string",
                        "description": "分类名称（可选）",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_stats",
            "description": "获取各分类的使用统计",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_retention_stats",
            "description": "获取用户留存分析数据，包括日留存、周留存、月留存",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["day", "week", "month"],
                        "description": "留存周期类型，默认 day",
                        "default": "day",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hourly_distribution",
            "description": "获取按小时的访问分布统计，了解用户活跃时段",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                },
                "required": [],
            },
        },
    },
    # ========== 新增工具 ==========
    {
        "type": "function",
        "function": {
            "name": "get_provider_stats",
            "description": "获取工具提供者/推荐者统计，看谁推荐的工具最多、最受欢迎",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tool_interactions",
            "description": "获取工具互动排行，按收藏数+点赞数排序，了解最受喜爱的工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hot_tools",
            "description": "获取热门新工具，查看最近新上架且点击量高的工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "查看最近N天新增的工具，默认7天",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_want_list",
            "description": "获取用户想要的工具列表，了解用户的工具需求和诉求",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认30天",
                        "default": 30,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认20",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_search_keywords",
            "description": "获取搜索热词统计，了解用户都在搜什么，哪些搜索有结果哪些没有",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认20",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_by_scenario",
            "description": "根据使用场景推荐工具，如画图、写代码、翻译等",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "description": "使用场景描述，如：画图、写代码、翻译、聊天",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量，默认5",
                        "default": 5,
                    },
                },
                "required": ["scenario"],
            },
        },
    },
]


def get_tools() -> list[dict[str, Any]]:
    """获取所有 MCP 工具定义"""
    return MCP_TOOLS


def get_tool_names() -> list[str]:
    """获取所有工具名称"""
    return [tool["function"]["name"] for tool in MCP_TOOLS]
