#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import fetch
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(CronTrigger.from_crontab("* * 2 * *"))
async def fetch_scheduler() -> None:
    print("fetch scheduler start...")
    await fetch.run()
    print("fetch scheduler end...")
