# 项目更新日志

## 2026-01-05

### 新增 Bot-Pilot 飞书机器人服务
- [新服务] 创建 `bot-pilot/` 独立服务目录，端口 8001
- [机器人] 飞书事件回调接口 (`/api/callback`)，支持 v1/v2 格式
- [机器人] 消息处理核心：事件去重、@机器人识别、快捷命令
- [AI] 集成 OpenAI API (gpt-4o)，支持多轮对话上下文
- [AI] System Prompt 角色限定：只回答 AI 导航相关问题
- [MCP] 10 个数据查询工具：概览/排行/趋势/留存/时段分布等
- [MCP] 工具执行器桥接 StatsService，复用现有统计能力
- [统计] 新增留存分析 (日/周/月留存率)
- [统计] 新增时段分布分析 (24小时访问分布)
- [卡片] CardBuilder 构建精美飞书卡片：概览/排行/搜索/留存/时段
- [部署] 新增 Dockerfile，集成到 docker-compose.yml
- [配置] 更新 .env.example 添加 OpenAI 配置
- [文档] 更新 CLAUDE.md，完整 README 和 .env.example

## 2026-01-04

### UI优化与功能增强
- [前端] ToolCard 新增提供者信息展示和详情按钮
- [前端] 新增 ToolDetailDialog 组件：工具详情弹窗，展示完整工具信息
- [前端] Home.vue Tab名称优化：目录→分类浏览，全局→全部工具
- [前端] 分类菜单工具计数改为角标样式：渐变背景、圆角设计

### 报表推送功能
- [前端] Admin后台移除返回首页按钮，新增报表推送菜单项
- [前端] 新增 ReportPush.vue 管理页面：推送设置、人员管理、手动推送、历史记录
- [后端] 新增 report_push.py 模型：推送设置、接收人、推送历史
- [后端] 新增 report_push.py API：设置管理、人员CRUD、推送/预览、历史查询
- [后端] feishu_service 扩展：通过邮箱获取用户、发送带附件的文件消息
- [后端] 支持飞书卡片消息和Excel文件两种推送方式

### 搜索历史功能
- [后端] 新增 search_history.py 模型：用户搜索历史记录
- [后端] 扩展 interactions.py API：搜索历史CRUD接口（获取/添加/删除/清空）
- [后端] 扩展 interaction.py schema：SearchHistoryItem、SearchHistoryResponse
- [前端] 新增 useSearchHistory.js composable：搜索历史状态管理
- [前端] Home.vue 搜索面板升级：搜索历史列表 + 热门搜索，支持删除/清空

### 数据统计与导出功能
- [后端] 新增 export_service.py：工具/用户/趋势数据 Excel 导出服务
- [后端] 扩展 stats_service.py：分类使用分布统计、单工具详细统计
- [后端] 扩展 admin.py API：分类分布、工具详情、三类报表导出接口
- [前端] 扩展 api/index.js：新增导出和分类分布 API 封装
- [前端] Stats.vue 全面升级：导出下拉按钮、分类饼图、工具表格增加UV列、用户头像展示

### UI/UX 全面优化
- [前端] ToolCard 组件重设计：热门标签(HOT)、NEW标签、热度指示条、渐变图标背景
- [前端] Home.vue 布局升级：玻璃拟态顶栏、现代化模式切换、圆角阴影搜索框
- [前端] 新增深色模式：useTheme composable + CSS变量体系，支持 localStorage 持久化
- [前端] 新增搜索热词推荐：基于热门工具名称的快捷搜索入口
- [前端] 新增键盘快捷键：useKeyboardNav composable，支持 `/` `Ctrl+K` `D` `H` `F` `Esc` `?`
- [前端] 快捷键帮助面板：浮动按钮 + 模态弹窗展示所有快捷键

### Bug 修复与优化
- [前端] API 异常处理增强：错误消息映射、超时/网络错误检测、401自动登出、静默请求支持
- [前端] Dashboard.vue 图表内存泄漏修复：resize 事件清理、ECharts 实例销毁、keep-alive 支持
- [前端] 修复 Home.vue Keyboard 图标导入错误，替换为 QuestionFilled

### 页面UI统一优化
- [前端] Favorites.vue 支持深色模式：CSS变量体系、现代化卡片悬停效果
- [前端] admin/Login.vue 全面重设计：背景装饰动画、玻璃拟态登录框、渐变按钮、移动端适配
- [前端] admin/Layout.vue 管理后台布局升级：深色侧边栏渐变、菜单项圆角高亮、页面标题样式优化
- [前端] FeedbackDialog.vue 重设计：工具信息横幅、卡片式类型选择器、渐变弹窗头部
- [前端] WantToolDialog.vue 重设计：顶部提示区、图标输入框、统一弹窗样式
- [前端] ToolCard.vue 按钮优化：渐变背景、边框高亮、弹跳动画、深色模式适配、移动端竖向布局

### 匿名交互模式
- [后端] config.py 新增 ALLOW_ANONYMOUS_INTERACTION 配置项
- [后端] interactions.py 新增 get_or_create_anonymous_user：匿名用户创建与复用
- [后端] interactions.py 改造 get_current_user/get_optional_user：支持匿名模式回退
- [后端] main.py 新增 /api/config 公开配置接口
- [前端] 新增 stores/config.js：应用配置状态管理
- [前端] App.vue 初始化加载应用配置
- [前端] ToolCard.vue 交互按钮改用 canInteract 判断：支持匿名模式下收藏/点赞/反馈

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
