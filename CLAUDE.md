# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

飞书工作台H5网页应用，提供AI工具导航和使用统计功能。前后端分离架构，支持飞书免登认证。
包含三个服务：frontend (Vue3)、backend (FastAPI)、bot-pilot (飞书机器人)。

## 常用命令

### 后端开发
```bash
cd backend
uv sync                                    # 安装依赖（使用uv）
uv run uvicorn app.main:app --reload --port 8000  # 启动开发服务器
```

### 前端开发
```bash
cd frontend
npm install                # 安装依赖
npm run dev               # 启动开发服务器 (端口3000)
npm run build             # 生产构建
```

### 机器人服务开发
```bash
cd bot-pilot
uv sync                                    # 安装依赖
uv run uvicorn app.main:app --reload --port 8001  # 启动开发服务器
```

### 数据库初始化
```bash
# PostgreSQL
psql -U postgres -f sql/init.sql

# SQLite（开发模式自动建表）
# 设置 DATABASE_URL=sqlite:///./dev.db
```

### Docker部署
```bash
cp .env.example .env       # 配置环境变量
docker-compose up -d       # 启动所有服务 (frontend, backend, bot-pilot)
```

## 架构概览

### 后端结构 (FastAPI)
```
backend/app/
├── main.py              # 应用入口，lifespan管理
├── config.py            # pydantic-settings配置（从.env读取）
├── database.py          # SQLAlchemy异步引擎
├── api/                 # 路由层
│   ├── auth.py         # 飞书用户认证
│   ├── admin_auth.py   # 管理员账密认证
│   ├── tools.py        # 工具CRUD
│   ├── categories.py   # 分类管理
│   ├── interactions.py # 收藏/点赞
│   ├── feedback.py     # 用户反馈
│   └── admin.py        # 管理后台API
├── models/              # SQLAlchemy ORM模型
├── schemas/             # Pydantic请求/响应模型
├── services/            # 业务逻辑层
│   ├── feishu_service.py  # 飞书API封装（token/用户信息）
│   ├── push_service.py    # 飞书消息推送
│   └── stats_service.py   # 统计服务
└── tasks/               # APScheduler定时任务
    ├── scheduler.py     # 调度器初始化
    └── report_task.py   # 定时推送统计报告
```

### 前端结构 (Vue 3 + Vite)
```
frontend/src/
├── App.vue             # 根组件，初始化飞书SDK
├── router/index.js     # 路由配置（含管理后台守卫）
├── stores/             # Pinia状态管理
│   ├── user.js        # 用户状态
│   └── admin.js       # 管理员状态
├── api/index.js        # axios封装
├── utils/feishu.js     # 飞书JSSDK初始化
├── views/
│   ├── Home.vue       # 工具导航首页
│   ├── Favorites.vue  # 收藏页
│   └── admin/         # 管理后台
│       ├── Layout.vue # 后台布局
│       ├── Dashboard.vue
│       ├── Tools.vue
│       ├── Categories.vue
│       ├── Stats.vue
│       └── Feedback.vue
└── components/
    ├── ToolCard.vue   # 工具卡片组件
    └── FeedbackDialog.vue
```

### 机器人服务结构 (Bot-Pilot)
```
bot-pilot/app/
├── main.py              # 应用入口
├── config.py            # 配置管理
├── api/
│   ├── callback.py     # 飞书事件回调
│   └── health.py       # 健康检查
├── core/
│   ├── event_handler.py    # 事件处理器
│   └── message_handler.py  # 消息处理
├── llm/
│   ├── chat_service.py     # OpenAI 聊天服务
│   ├── mcp_tools.py        # MCP 工具定义 (10个)
│   ├── prompt_manager.py   # System Prompt
│   └── tool_executor.py    # 工具执行器
├── services/
│   ├── database.py         # 数据库连接
│   ├── feishu_client.py    # 飞书客户端
│   └── stats_bridge.py     # 统计服务桥接
└── cards/
    └── builder.py          # 卡片消息构建器
```

## 关键设计

### 双数据库支持
- 开发：SQLite（自动建表，无需init.sql）
- 生产：PostgreSQL（asyncpg驱动）
- 配置切换：`DATABASE_URL` 环境变量

### 认证机制
- 用户端：飞书免登（code换token → 获取用户信息）
- 管理后台：独立账密认证（admin_users表）

### API代理
前端开发时，vite.config.js配置 `/api` 代理到后端8000端口

### 机器人触发方式
- 私聊：直接发消息
- 群聊：@机器人 + 消息

## 环境变量

| 变量 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用ID |
| `FEISHU_APP_SECRET` | 飞书应用密钥 |
| `DATABASE_URL` | 数据库连接串 |
| `ADMIN_OPEN_IDS` | 管理员open_id列表（逗号分隔） |
| `PUSH_CHAT_ID` | 统计推送目标群ID |
| `PUSH_CRON` | 推送cron表达式 |
| `OPENAI_API_KEY` | OpenAI API密钥 (bot-pilot) |
| `OPENAI_MODEL` | OpenAI模型 (默认gpt-4o) |
