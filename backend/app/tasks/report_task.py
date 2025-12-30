"""报告生成任务"""
import logging
from datetime import datetime

from ..database import async_session
from ..services.stats_service import StatsService
from ..services.push_service import push_service

logger = logging.getLogger(__name__)


async def daily_report_task():
    """生成并推送每日统计报告"""
    logger.info("开始执行每日报告任务")

    try:
        async with async_session() as db:
            stats_service = StatsService(db)

            # 生成报告数据
            report = await stats_service.generate_daily_report()

            # 推送到飞书
            success = await push_service.push_daily_report(report)

            if success:
                logger.info(f"每日报告推送成功: {report}")
            else:
                logger.warning("每日报告推送失败")

    except Exception as e:
        logger.error(f"每日报告任务执行失败: {e}", exc_info=True)
