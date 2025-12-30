-- 飞书AI工具导航栏 - 数据库初始化脚本

-- 分类表（支持两级）
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_id INT REFERENCES categories(id),
    icon_url VARCHAR(500),
    color VARCHAR(20),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_sort ON categories(sort_order);

-- 工具表
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    target_url VARCHAR(1000) NOT NULL,
    category_id INT REFERENCES categories(id),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    -- 权限扩展预留
    visible_departments JSONB,
    visible_roles JSONB,
    -- 审计字段
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_tools_active ON tools(is_active);
CREATE INDEX IF NOT EXISTS idx_tools_sort ON tools(sort_order);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    open_id VARCHAR(100) UNIQUE NOT NULL,
    union_id VARCHAR(100),
    user_id VARCHAR(100),
    name VARCHAR(100),
    avatar_url VARCHAR(500),
    department VARCHAR(200),
    first_visit_at TIMESTAMP DEFAULT NOW(),
    last_visit_at TIMESTAMP DEFAULT NOW(),
    visit_count INT DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_users_open_id ON users(open_id);

-- 点击日志表
CREATE TABLE IF NOT EXISTS click_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    tool_id INT REFERENCES tools(id),
    clicked_at TIMESTAMP DEFAULT NOW(),
    client_type VARCHAR(20),
    ip_address VARCHAR(50),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_click_logs_user ON click_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_click_logs_tool ON click_logs(tool_id);
CREATE INDEX IF NOT EXISTS idx_click_logs_time ON click_logs(clicked_at);
CREATE INDEX IF NOT EXISTS idx_click_logs_stats ON click_logs(tool_id, clicked_at);

-- 统计缓存表
CREATE TABLE IF NOT EXISTS statistics_cache (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    stat_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stat_date, stat_type)
);

-- 插入示例分类
INSERT INTO categories (name, icon_url, color, sort_order) VALUES
('AI对话', NULL, '#409eff', 1),
('AI绘画', NULL, '#67c23a', 2),
('AI效率', NULL, '#e6a23c', 3)
ON CONFLICT DO NOTHING;

-- 插入二级分类
INSERT INTO categories (name, parent_id, color, sort_order) VALUES
('通用对话', 1, '#409eff', 1),
('代码助手', 1, '#409eff', 2),
('图像生成', 2, '#67c23a', 1),
('写作助手', 3, '#e6a23c', 1)
ON CONFLICT DO NOTHING;

-- 插入示例工具
INSERT INTO tools (name, description, target_url, category_id, sort_order) VALUES
('ChatGPT', 'OpenAI对话助手', 'https://chat.openai.com', 4, 1),
('Claude', 'Anthropic智能助手', 'https://claude.ai', 4, 2),
('GitHub Copilot', 'AI代码补全', 'https://github.com/features/copilot', 5, 1),
('Midjourney', 'AI图像生成', 'https://midjourney.com', 6, 1),
('Notion AI', '智能笔记助手', 'https://notion.so', 7, 1)
ON CONFLICT DO NOTHING;
