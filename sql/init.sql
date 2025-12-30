-- 飞书AI工具导航栏 - 数据库初始化脚本

-- 工具表
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    target_url VARCHAR(1000) NOT NULL,
    category VARCHAR(50),
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

-- 插入示例数据
INSERT INTO tools (name, description, icon_url, target_url, sort_order) VALUES
('ChatGPT', 'OpenAI对话助手', 'https://cdn.example.com/icons/chatgpt.png', 'https://chat.openai.com', 1),
('Claude', 'Anthropic智能助手', 'https://cdn.example.com/icons/claude.png', 'https://claude.ai', 2),
('Midjourney', 'AI图像生成', 'https://cdn.example.com/icons/mj.png', 'https://midjourney.com', 3),
('Notion AI', '智能笔记助手', 'https://cdn.example.com/icons/notion.png', 'https://notion.so', 4)
ON CONFLICT DO NOTHING;
