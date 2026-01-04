"""数据导出服务"""
import io
from datetime import date, datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models import Tool, User, Category, ClickLog, UserFavorite, UserLike
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """数据导出服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_tools_stats(self, days: int = 30) -> bytes:
        """导出工具统计报表"""
        start_date = datetime.now() - timedelta(days=days)

        # 查询工具统计数据
        query = (
            select(
                Tool.id,
                Tool.name,
                Category.name.label("category_name"),
                func.count(ClickLog.id).label("pv"),
                func.count(distinct(ClickLog.user_id)).label("uv"),
            )
            .outerjoin(Category, Tool.category_id == Category.id)
            .outerjoin(ClickLog, Tool.id == ClickLog.tool_id)
            .where(Tool.is_active == True)
            .group_by(Tool.id, Tool.name, Category.name)
            .order_by(func.count(ClickLog.id).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 获取收藏和点赞数
        fav_query = (
            select(UserFavorite.tool_id, func.count(UserFavorite.id).label("count"))
            .group_by(UserFavorite.tool_id)
        )
        fav_result = await self.db.execute(fav_query)
        fav_map = {row.tool_id: row.count for row in fav_result.all()}

        like_query = (
            select(UserLike.tool_id, func.count(UserLike.id).label("count"))
            .group_by(UserLike.tool_id)
        )
        like_result = await self.db.execute(like_query)
        like_map = {row.tool_id: row.count for row in like_result.all()}

        # 创建 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "工具统计"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 写入表头
        headers = ["工具ID", "工具名称", "分类", "PV(浏览量)", "UV(独立访客)", "收藏数", "点赞数"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 写入数据
        for row_idx, row in enumerate(rows, 2):
            ws.cell(row=row_idx, column=1, value=row.id).border = thin_border
            ws.cell(row=row_idx, column=2, value=row.name).border = thin_border
            ws.cell(row=row_idx, column=3, value=row.category_name or "未分类").border = thin_border
            ws.cell(row=row_idx, column=4, value=row.pv or 0).border = thin_border
            ws.cell(row=row_idx, column=5, value=row.uv or 0).border = thin_border
            ws.cell(row=row_idx, column=6, value=fav_map.get(row.id, 0)).border = thin_border
            ws.cell(row=row_idx, column=7, value=like_map.get(row.id, 0)).border = thin_border

        # 调整列宽
        column_widths = [10, 25, 15, 15, 15, 12, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()

    async def export_users_stats(self, days: int = 30) -> bytes:
        """导出用户统计报表"""
        start_date = datetime.now() - timedelta(days=days)

        # 查询用户统计数据
        query = (
            select(
                User.id,
                User.name,
                User.department,
                User.first_visit_at,
                User.last_visit_at,
                User.visit_count,
                func.count(ClickLog.id).label("click_count"),
                func.count(distinct(ClickLog.tool_id)).label("tool_count"),
            )
            .outerjoin(ClickLog, User.id == ClickLog.user_id)
            .group_by(User.id, User.name, User.department, User.first_visit_at, User.last_visit_at, User.visit_count)
            .order_by(func.count(ClickLog.id).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 获取收藏数
        fav_query = (
            select(UserFavorite.user_id, func.count(UserFavorite.id).label("count"))
            .group_by(UserFavorite.user_id)
        )
        fav_result = await self.db.execute(fav_query)
        fav_map = {row.user_id: row.count for row in fav_result.all()}

        # 创建 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "用户统计"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 写入表头
        headers = ["用户ID", "用户名", "部门", "首次访问", "最后访问", "访问次数", "点击数", "使用工具数", "收藏数"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 写入数据
        def format_datetime(dt):
            if not dt:
                return ""
            if isinstance(dt, str):
                return dt[:16]
            return dt.strftime("%Y-%m-%d %H:%M")

        for row_idx, row in enumerate(rows, 2):
            ws.cell(row=row_idx, column=1, value=row.id).border = thin_border
            ws.cell(row=row_idx, column=2, value=row.name or "未知").border = thin_border
            ws.cell(row=row_idx, column=3, value=row.department or "").border = thin_border
            ws.cell(row=row_idx, column=4, value=format_datetime(row.first_visit_at)).border = thin_border
            ws.cell(row=row_idx, column=5, value=format_datetime(row.last_visit_at)).border = thin_border
            ws.cell(row=row_idx, column=6, value=row.visit_count or 0).border = thin_border
            ws.cell(row=row_idx, column=7, value=row.click_count or 0).border = thin_border
            ws.cell(row=row_idx, column=8, value=row.tool_count or 0).border = thin_border
            ws.cell(row=row_idx, column=9, value=fav_map.get(row.id, 0)).border = thin_border

        # 调整列宽
        column_widths = [10, 20, 20, 18, 18, 12, 12, 14, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()

    async def export_trend_stats(self, days: int = 30) -> bytes:
        """导出趋势统计报表"""
        start_date = datetime.now() - timedelta(days=days)

        # 查询趋势数据
        query = (
            select(
                func.date(ClickLog.clicked_at).label("date"),
                func.count(ClickLog.id).label("pv"),
                func.count(distinct(ClickLog.user_id)).label("uv"),
            )
            .where(ClickLog.clicked_at >= start_date)
            .group_by(func.date(ClickLog.clicked_at))
            .order_by(func.date(ClickLog.clicked_at))
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 创建 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "趋势统计"

        # 表头样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # 写入表头
        headers = ["日期", "PV(浏览量)", "UV(独立访客)"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 写入数据
        for row_idx, row in enumerate(rows, 2):
            date_str = row.date if isinstance(row.date, str) else row.date.isoformat()
            ws.cell(row=row_idx, column=1, value=date_str).border = thin_border
            ws.cell(row=row_idx, column=2, value=row.pv or 0).border = thin_border
            ws.cell(row=row_idx, column=3, value=row.uv or 0).border = thin_border

        # 调整列宽
        column_widths = [15, 15, 15]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.read()
