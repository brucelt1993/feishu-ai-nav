# 飞书AI工具导航栏

飞书工作台H5网页应用，提供AI工具导航入口和使用统计功能。

## 功能特性

- 飞书免登认证
- AI工具卡片导航
- 点击统计与分析
- 管理后台（工具CRUD、数据可视化）
- 定时推送统计报告到飞书

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + ECharts
- **后端**: FastAPI + SQLAlchemy + APScheduler
- **数据库**: PostgreSQL
- **部署**: Docker + Nginx

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker (可选)

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### Docker部署

```bash
# 复制环境变量
cp .env.example .env
# 编辑 .env 填入飞书应用凭证

# 启动服务
docker-compose up -d
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用App ID |
| `FEISHU_APP_SECRET` | 飞书应用App Secret |
| `DATABASE_URL` | PostgreSQL连接字符串 |
| `ADMIN_OPEN_IDS` | 管理员open_id列表（逗号分隔） |
| `PUSH_CHAT_ID` | 统计推送目标群chat_id |

## 飞书应用配置

1. 登录[飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 添加「网页应用」能力
4. 配置：
   - 主页URL: `https://你的域名/`
   - H5可信域名: `你的域名`
   - 重定向URL: `https://你的域名/auth/callback`
5. 申请权限：获取用户基本信息
6. 发布应用

## 项目结构

```
feishu-ai-nav/
├── frontend/           # Vue3前端
├── backend/            # FastAPI后端
├── sql/                # 数据库脚本
├── docker-compose.yml
├── nginx.conf
└── .env.example
```

## License

MIT
