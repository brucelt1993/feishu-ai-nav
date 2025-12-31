"""创建管理员账号脚本"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session
from app.models import AdminUser
from app.api.admin_auth import hash_password


async def create_admin(username: str, password: str, nickname: str = None):
    """创建管理员账号"""
    async with async_session() as db:
        # 检查是否已存在
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"❌ 管理员 '{username}' 已存在!")
            return False

        # 创建新管理员
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            nickname=nickname or username,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

        print(f"✅ 管理员创建成功!")
        print(f"   用户名: {username}")
        print(f"   昵称: {nickname or username}")
        return True


async def list_admins():
    """列出所有管理员"""
    async with async_session() as db:
        result = await db.execute(select(AdminUser))
        admins = result.scalars().all()

        if not admins:
            print("暂无管理员账号")
            return

        print("\n管理员列表:")
        print("-" * 50)
        for admin in admins:
            status = "✓ 启用" if admin.is_active else "✗ 禁用"
            print(f"  [{admin.id}] {admin.username} ({admin.nickname}) - {status}")
        print("-" * 50)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/create_admin.py create <username> <password> [nickname]")
        print("  python scripts/create_admin.py list")
        print()
        print("示例:")
        print("  python scripts/create_admin.py create admin 123456 管理员")
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 4:
            print("❌ 请提供用户名和密码")
            print("用法: python scripts/create_admin.py create <username> <password> [nickname]")
            return
        username = sys.argv[2]
        password = sys.argv[3]
        nickname = sys.argv[4] if len(sys.argv) > 4 else None
        asyncio.run(create_admin(username, password, nickname))

    elif command == "list":
        asyncio.run(list_admins())

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
