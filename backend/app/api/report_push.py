"""报表推送管理API"""
import io
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import ReportPushSettings, ReportRecipient, ReportPushHistory
from app.api.admin import verify_admin
from app.services.stats_service import StatsService
from app.services.feishu_service import feishu_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/report-push", tags=["报表推送"])


# ============ Schemas ============
class SettingsUpdate(BaseModel):
    enabled: bool = False
    push_time: Optional[str] = None
    report_types: Optional[List[str]] = None
    days: Optional[int] = 7


class RecipientCreate(BaseModel):
    name: str
    email: EmailStr


class RecipientUpdate(BaseModel):
    is_active: Optional[bool] = None


class PushRequest(BaseModel):
    report_types: List[str]
    days: int = 7
    method: str = "feishu"  # feishu or email


class PreviewRequest(BaseModel):
    report_types: List[str]
    days: int = 7


# ============ 设置管理 ============
@router.get("/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """获取推送设置"""
    result = await db.execute(select(ReportPushSettings).limit(1))
    settings = result.scalar_one_or_none()

    if not settings:
        return {
            "enabled": False,
            "push_time": None,
            "report_types": ["overview", "tools"],
            "days": 7
        }

    return {
        "enabled": settings.enabled,
        "push_time": settings.push_time,
        "report_types": settings.report_types.split(",") if settings.report_types else ["overview", "tools"],
        "days": settings.days or 7
    }


@router.put("/settings")
async def update_settings(
    data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """更新推送设置"""
    result = await db.execute(select(ReportPushSettings).limit(1))
    settings = result.scalar_one_or_none()

    report_types_str = ",".join(data.report_types) if data.report_types else "overview,tools"

    if not settings:
        settings = ReportPushSettings(
            enabled=data.enabled,
            push_time=data.push_time,
            report_types=report_types_str,
            days=data.days or 7
        )
        db.add(settings)
    else:
        settings.enabled = data.enabled
        settings.push_time = data.push_time
        settings.report_types = report_types_str
        settings.days = data.days or 7
        settings.updated_at = datetime.utcnow()

    await db.commit()
    return {"message": "设置已更新"}


# ============ 接收人管理 ============
@router.get("/recipients")
async def get_recipients(
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """获取推送接收人列表"""
    result = await db.execute(
        select(ReportRecipient).order_by(ReportRecipient.created_at.desc())
    )
    recipients = result.scalars().all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in recipients
    ]


@router.post("/recipients")
async def add_recipient(
    data: RecipientCreate,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """添加推送接收人"""
    # 检查邮箱是否已存在
    result = await db.execute(
        select(ReportRecipient).where(ReportRecipient.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已存在")

    recipient = ReportRecipient(name=data.name, email=data.email)
    db.add(recipient)
    await db.commit()
    await db.refresh(recipient)

    return {
        "id": recipient.id,
        "name": recipient.name,
        "email": recipient.email,
        "is_active": recipient.is_active,
        "created_at": recipient.created_at.isoformat()
    }


@router.put("/recipients/{recipient_id}")
async def update_recipient(
    recipient_id: int,
    data: RecipientUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """更新推送接收人"""
    result = await db.execute(
        select(ReportRecipient).where(ReportRecipient.id == recipient_id)
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="接收人不存在")

    if data.is_active is not None:
        recipient.is_active = data.is_active

    recipient.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "更新成功"}


@router.delete("/recipients/{recipient_id}")
async def delete_recipient(
    recipient_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """删除推送接收人"""
    result = await db.execute(
        select(ReportRecipient).where(ReportRecipient.id == recipient_id)
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="接收人不存在")

    await db.delete(recipient)
    await db.commit()

    return {"message": "删除成功"}


# ============ 推送历史 ============
@router.get("/history")
async def get_history(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """获取推送历史"""
    offset = (page - 1) * size

    # 总数
    count_result = await db.execute(select(func.count(ReportPushHistory.id)))
    total = count_result.scalar()

    # 列表
    result = await db.execute(
        select(ReportPushHistory)
        .order_by(ReportPushHistory.pushed_at.desc())
        .offset(offset)
        .limit(size)
    )
    items = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": h.id,
                "report_type": h.report_type,
                "push_method": h.push_method,
                "recipient_count": h.recipient_count,
                "status": h.status,
                "error_msg": h.error_msg,
                "pushed_at": h.pushed_at.isoformat() if h.pushed_at else None
            }
            for h in items
        ]
    }


# ============ 推送和预览 ============
@router.post("/preview")
async def preview_report(
    data: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """预览报表数据"""
    stats_service = StatsService(db)
    result = {}

    if "overview" in data.report_types:
        result["overview"] = await stats_service.get_overview()

    if "tools" in data.report_types:
        result["tools"] = await stats_service.get_tool_stats(days=data.days, limit=10)

    if "users" in data.report_types:
        result["users"] = await stats_service.get_user_stats(days=data.days, limit=10)

    if "trend" in data.report_types:
        result["trend"] = await stats_service.get_trend(days=data.days)

    return result


@router.post("/push")
async def push_report(
    data: PushRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _admin: str = Depends(verify_admin)
):
    """推送报表"""
    # 获取活跃的接收人
    result = await db.execute(
        select(ReportRecipient).where(ReportRecipient.is_active == True)
    )
    recipient_objs = result.scalars().all()

    if not recipient_objs:
        raise HTTPException(status_code=400, detail="没有可用的推送接收人")

    # 转换为字典，避免后台任务中 session 关闭后无法访问 ORM 属性
    recipients = [{"name": r.name, "email": r.email} for r in recipient_objs]

    # 获取报表数据
    stats_service = StatsService(db)
    report_data = {}

    if "overview" in data.report_types:
        report_data["overview"] = await stats_service.get_overview()

    if "tools" in data.report_types:
        report_data["tools"] = await stats_service.get_tool_stats(days=data.days, limit=10)

    if "users" in data.report_types:
        report_data["users"] = await stats_service.get_user_stats(days=data.days, limit=10)

    if "trend" in data.report_types:
        report_data["trend"] = await stats_service.get_trend(days=data.days)

    # 记录推送历史
    history = ReportPushHistory(
        report_type=",".join(data.report_types),
        push_method=data.method,
        recipient_count=len(recipients),
        status="pending"
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    # 后台推送
    if data.method == "feishu":
        background_tasks.add_task(
            push_feishu_report,
            history.id,
            recipients,
            report_data,
            data.days
        )
    else:
        background_tasks.add_task(
            push_email_report,
            history.id,
            recipients,
            report_data,
            data.days
        )

    return {"message": "推送任务已提交", "history_id": history.id}


async def push_feishu_report(history_id: int, recipients: list, report_data: dict, days: int):
    """飞书消息推送"""
    from app.database import async_session

    async with async_session() as db:
        try:
            # 构建卡片消息
            card = build_report_card(report_data, days)

            # 逐个推送给接收人
            success_count = 0
            errors = []

            for recipient in recipients:
                try:
                    # 通过邮箱获取用户open_id
                    user_info = await feishu_service.get_user_by_email(recipient["email"])
                    if user_info and user_info.get("open_id"):
                        await feishu_service.send_card_message(
                            user_info["open_id"],
                            card,
                            receive_id_type="open_id"
                        )
                        success_count += 1
                    else:
                        errors.append(f"{recipient['name']}: 未找到飞书用户")
                except Exception as e:
                    errors.append(f"{recipient['name']}: {str(e)}")
                    logger.error(f"推送给 {recipient['name']} 失败: {e}")

            # 更新历史记录
            result = await db.execute(
                select(ReportPushHistory).where(ReportPushHistory.id == history_id)
            )
            history = result.scalar_one_or_none()
            if history:
                if success_count > 0:
                    history.status = "success"
                    if errors:
                        history.error_msg = f"部分成功({success_count}/{len(recipients)}): " + "; ".join(errors)
                else:
                    history.status = "failed"
                    history.error_msg = "; ".join(errors)
                await db.commit()

            logger.info(f"飞书推送完成: {success_count}/{len(recipients)}")

        except Exception as e:
            logger.error(f"飞书推送失败: {e}")
            result = await db.execute(
                select(ReportPushHistory).where(ReportPushHistory.id == history_id)
            )
            history = result.scalar_one_or_none()
            if history:
                history.status = "failed"
                history.error_msg = str(e)
                await db.commit()


async def push_email_report(history_id: int, recipients: list, report_data: dict, days: int):
    """邮件推送(Excel附件)"""
    from app.database import async_session

    async with async_session() as db:
        try:
            # 生成Excel文件
            excel_content = generate_report_excel(report_data, days)

            # 逐个发送邮件
            success_count = 0
            errors = []

            for recipient in recipients:
                try:
                    # 通过飞书邮件API发送
                    await feishu_service.send_email_with_attachment(
                        to_email=recipient["email"],
                        subject=f"AI工具导航统计报表 - 近{days}天",
                        content="请查看附件中的统计报表。",
                        attachment_name=f"report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        attachment_content=excel_content
                    )
                    success_count += 1
                except Exception as e:
                    errors.append(f"{recipient['name']}: {str(e)}")
                    logger.error(f"发送邮件给 {recipient['name']} 失败: {e}")

            # 更新历史记录
            result = await db.execute(
                select(ReportPushHistory).where(ReportPushHistory.id == history_id)
            )
            history = result.scalar_one_or_none()
            if history:
                if success_count > 0:
                    history.status = "success"
                    if errors:
                        history.error_msg = f"部分成功({success_count}/{len(recipients)}): " + "; ".join(errors)
                else:
                    history.status = "failed"
                    history.error_msg = "; ".join(errors)
                await db.commit()

            logger.info(f"邮件推送完成: {success_count}/{len(recipients)}")

        except Exception as e:
            logger.error(f"邮件推送失败: {e}")
            result = await db.execute(
                select(ReportPushHistory).where(ReportPushHistory.id == history_id)
            )
            history = result.scalar_one_or_none()
            if history:
                history.status = "failed"
                history.error_msg = str(e)
                await db.commit()


def build_report_card(report_data: dict, days: int) -> dict:
    """构建飞书卡片消息"""
    elements = []

    # 标题
    elements.append({
        "tag": "markdown",
        "content": f"**📊 AI工具导航统计报表（近{days}天）**"
    })

    elements.append({"tag": "hr"})

    # 概览
    if "overview" in report_data:
        overview = report_data["overview"]
        elements.append({
            "tag": "markdown",
            "content": (
                f"**数据概览**\n"
                f"• 总PV: {overview.get('total_pv', 0)}\n"
                f"• 总UV: {overview.get('total_uv', 0)}\n"
                f"• 今日PV: {overview.get('today_pv', 0)}\n"
                f"• 今日UV: {overview.get('today_uv', 0)}"
            )
        })

    # 工具排行
    if "tools" in report_data and report_data["tools"]:
        tools = report_data["tools"][:5]
        tool_lines = "\n".join([
            f"{i+1}. {t['tool_name']}: {t['click_count']}次"
            for i, t in enumerate(tools)
        ])
        elements.append({
            "tag": "markdown",
            "content": f"**🔥 工具排行 TOP5**\n{tool_lines}"
        })

    # 用户排行
    if "users" in report_data and report_data["users"]:
        users = report_data["users"][:5]
        user_lines = "\n".join([
            f"{i+1}. {u['user_name']}: {u['click_count']}次"
            for i, u in enumerate(users)
        ])
        elements.append({
            "tag": "markdown",
            "content": f"**👥 活跃用户 TOP5**\n{user_lines}"
        })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"content": "📊 统计报表", "tag": "plain_text"},
            "template": "blue"
        },
        "elements": elements
    }


def generate_report_excel(report_data: dict, days: int) -> bytes:
    """生成Excel报表"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
    except ImportError:
        raise HTTPException(status_code=500, detail="Excel库未安装")

    wb = openpyxl.Workbook()

    # 概览Sheet
    if "overview" in report_data:
        ws = wb.active
        ws.title = "数据概览"
        overview = report_data["overview"]

        headers = ["指标", "数值"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")

        data = [
            ("总PV", overview.get("total_pv", 0)),
            ("总UV", overview.get("total_uv", 0)),
            ("今日PV", overview.get("today_pv", 0)),
            ("今日UV", overview.get("today_uv", 0)),
            ("工具总数", overview.get("tool_count", 0)),
        ]
        for row, (label, value) in enumerate(data, 2):
            ws.cell(row=row, column=1, value=label)
            ws.cell(row=row, column=2, value=value)

    # 工具排行Sheet
    if "tools" in report_data and report_data["tools"]:
        ws = wb.create_sheet("工具排行")
        headers = ["排名", "工具名称", "点击次数"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")

        for row, tool in enumerate(report_data["tools"], 2):
            ws.cell(row=row, column=1, value=row - 1)
            ws.cell(row=row, column=2, value=tool.get("tool_name", ""))
            ws.cell(row=row, column=3, value=tool.get("click_count", 0))

    # 用户统计Sheet
    if "users" in report_data and report_data["users"]:
        ws = wb.create_sheet("用户统计")
        headers = ["排名", "用户名", "访问次数"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")

        for row, user in enumerate(report_data["users"], 2):
            ws.cell(row=row, column=1, value=row - 1)
            ws.cell(row=row, column=2, value=user.get("user_name", ""))
            ws.cell(row=row, column=3, value=user.get("click_count", 0))

    # 保存到字节流
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
