# 项目更新日志

## 2025-12-31

### Phase 2: 高级交互功能
- [后端] 新增 ToolFeedback 模型 (`models/feedback.py`) 支持用户反馈/诉求
- [后端] 新增反馈 API (`api/feedback.py`): 创建反馈、用户历史、管理员列表/处理/统计
- [后端] 注册反馈路由到 API Router
- [前端] 新增 WantToolDialog 组件 - "想要工具"弹窗
- [前端] 新增 FeedbackDialog 组件 - 针对已有工具的反馈弹窗
- [前端] 修改 ToolCard 添加反馈按钮
- [前端] 修改 Home.vue 添加"想要工具"入口按钮
- [前端] 新增 admin/Feedback.vue 反馈管理页面（含统计卡片、筛选、处理弹窗）
- [前端] 更新路由和布局添加反馈管理入口

### Phase 1: 收藏 + 点赞功能
- [后端] 新增 UserFavorite, UserLike 模型 (`models/user_interaction.py`)
- [后端] 新增交互 Schema (`schemas/interaction.py`)
- [后端] 新增交互 API (`api/interactions.py`): 收藏/取消、点赞/取消、统计
- [前端] 抽取 ToolCard 组件，集成点赞/收藏按钮
- [前端] 新增 Favorites.vue 收藏夹页面
- [前端] 更新 API 模块添加交互接口
- [前端] 添加收藏页路由和导航入口
