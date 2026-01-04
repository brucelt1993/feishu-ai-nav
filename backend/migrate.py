"""数据库迁移脚本 - 添加 P1/P2 新表（本地 SQLite）"""
import asyncio
from sqlalchemy import text
from app.database import engine, async_session

# SQLite 版本的建表语句
MIGRATIONS = [
    # P1: 用户收藏表
    """
    CREATE TABLE IF NOT EXISTS user_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tool_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_favorites_user ON user_favorites(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_favorites_tool ON user_favorites(tool_id)",

    # P1: 用户点赞表
    """
    CREATE TABLE IF NOT EXISTS user_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tool_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_likes_user ON user_likes(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_likes_tool ON user_likes(tool_id)",

    # P2: 工具反馈表
    """
    CREATE TABLE IF NOT EXISTS tool_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        tool_id INTEGER REFERENCES tools(id) ON DELETE SET NULL,
        feedback_type VARCHAR(20) NOT NULL,
        content TEXT,
        tool_name VARCHAR(100),
        tool_url VARCHAR(500),
        status VARCHAR(20) DEFAULT 'pending',
        admin_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_feedback_status ON tool_feedback(status)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_type ON tool_feedback(feedback_type)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_user ON tool_feedback(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_feedback_created ON tool_feedback(created_at)",

    # P4: 管理员用户表
    """
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        nickname VARCHAR(50),
        is_active BOOLEAN DEFAULT 1,
        last_login_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_admin_username ON admin_users(username)",

    # 工具表新增 provider 字段
    "ALTER TABLE tools ADD COLUMN provider VARCHAR(100)",

    # 报表推送设置表新增字段
    "ALTER TABLE report_push_settings ADD COLUMN report_types VARCHAR(100) DEFAULT 'overview,tools'",
    "ALTER TABLE report_push_settings ADD COLUMN days INTEGER DEFAULT 7",

    # 初始化管理员账号 (admin / krmbe4bb)
    """
    INSERT OR IGNORE INTO admin_users (username, password_hash, nickname, is_active)
    VALUES ('admin', '40125cb934e854f0cdf2e2dd5cf0bc5bc7f65f10a7eebdafe6d00836dbfb441f', '管理员', 1)
    """,
]


async def migrate():
    """执行迁移"""
    async with async_session() as db:
        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                await db.execute(text(sql.strip()))
                print(f"[{i}/{len(MIGRATIONS)}] OK")
            except Exception as e:
                print(f"[{i}/{len(MIGRATIONS)}] 跳过 (可能已存在): {str(e)[:50]}")

        await db.commit()

    print("\n迁移完成！")
    print("新增表:")
    print("  - user_favorites (用户收藏)")
    print("  - user_likes (用户点赞)")
    print("  - tool_feedback (工具反馈)")
    print("  - admin_users (管理员用户)")
    print("新增字段:")
    print("  - tools.provider (提供者)")
    print("初始管理员:")
    print("  - 用户名: admin")
    print("  - 密码: krmbe4bb")


if __name__ == "__main__":
    asyncio.run(migrate())
