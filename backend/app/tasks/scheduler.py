"""定时任务调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from .report_task import daily_report_task

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def init_scheduler():
    """初始化定时任务"""
    # 每天早上9点执行日报推送
    scheduler.add_job(
        daily_report_task,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_report",
        name="每日统计报告推送",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("定时任务调度器已启动")


def shutdown_scheduler():
    """关闭定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
