"""初始化数据库示例数据"""
import asyncio
from sqlalchemy import select
from app.database import async_session, init_db
from app.models import Category, Tool


async def seed():
    """插入示例数据"""
    # 先建表
    await init_db()

    async with async_session() as db:
        # 检查是否已有数据
        result = await db.execute(select(Category).limit(1))
        if result.scalar():
            print("数据库已有数据，跳过初始化")
            return

        # 创建一级分类
        cat_chat = Category(name="AI对话", color="#409eff", sort_order=1)
        cat_draw = Category(name="AI绘画", color="#67c23a", sort_order=2)
        cat_eff = Category(name="AI效率", color="#e6a23c", sort_order=3)

        db.add_all([cat_chat, cat_draw, cat_eff])
        await db.flush()

        # 创建二级分类
        sub_general = Category(name="通用对话", parent_id=cat_chat.id, color="#409eff", sort_order=1)
        sub_code = Category(name="代码助手", parent_id=cat_chat.id, color="#409eff", sort_order=2)
        sub_image = Category(name="图像生成", parent_id=cat_draw.id, color="#67c23a", sort_order=1)
        sub_write = Category(name="写作助手", parent_id=cat_eff.id, color="#e6a23c", sort_order=1)

        db.add_all([sub_general, sub_code, sub_image, sub_write])
        await db.flush()

        # 创建示例工具
        tools = [
            Tool(
                name="ChatGPT",
                description="OpenAI对话助手",
                target_url="https://chat.openai.com",
                category_id=sub_general.id,
                sort_order=1,
            ),
            Tool(
                name="Claude",
                description="Anthropic智能助手",
                target_url="https://claude.ai",
                category_id=sub_general.id,
                sort_order=2,
            ),
            Tool(
                name="GitHub Copilot",
                description="AI代码补全",
                target_url="https://github.com/features/copilot",
                category_id=sub_code.id,
                sort_order=1,
            ),
            Tool(
                name="Midjourney",
                description="AI图像生成",
                target_url="https://midjourney.com",
                category_id=sub_image.id,
                sort_order=1,
            ),
            Tool(
                name="DALL-E",
                description="OpenAI图像生成",
                target_url="https://openai.com/dall-e-3",
                category_id=sub_image.id,
                sort_order=2,
            ),
            Tool(
                name="Notion AI",
                description="智能笔记助手",
                target_url="https://notion.so",
                category_id=sub_write.id,
                sort_order=1,
            ),
        ]

        db.add_all(tools)
        await db.commit()

        print("初始化完成！")
        print(f"  - 3 个一级分类")
        print(f"  - 4 个二级分类")
        print(f"  - 6 个工具")


if __name__ == "__main__":
    asyncio.run(seed())
