#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from workday import fetch

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger.from_crontab("0 10 2 * *"))
async def fetch_scheduler() -> None:
    print("fetch scheduler start...")
    await fetch.run()
    print("fetch scheduler end...")
