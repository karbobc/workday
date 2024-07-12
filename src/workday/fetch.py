#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import itertools
import asyncio
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
from filelock import FileLock
from httpx import codes
from typing_extensions import TypedDict

session = httpx.AsyncClient()


class HolidayItem(TypedDict):
    name: str
    date: str
    isOffDay: bool


async def fetch_holiday(year: int | str = datetime.now().year) -> List[HolidayItem]:
    try:
        response = await session.get(
            f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json",
        )
        return (
            [] if response.status_code != codes.OK else response.json().get("days", [])
        )
    except httpx.TimeoutException:
        print("requests timeout")
        return []


async def fetch_workday(year: int | str = datetime.now().year) -> Dict[str, bool]:
    tasks = [
        asyncio.create_task(fetch_holiday(year - 1)),
        asyncio.create_task(fetch_holiday(year)),
        asyncio.create_task(fetch_holiday(year + 1)),
    ]
    results: Tuple[List[HolidayItem]] = await asyncio.gather(*tasks)
    holiday_data: List[HolidayItem] = list(itertools.chain.from_iterable(results))
    holiday_data_filter = list(filter(lambda x: int(x["date"][:4]) == int(year), holiday_data))
    data = {item["date"]: not item["isOffDay"] for item in holiday_data_filter}
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current_date = start_date
    while current_date <= end_date:
        formatted_date = current_date.strftime("%Y-%m-%d")
        if data.get(formatted_date) is None:
            data.update({formatted_date: current_date.weekday() not in [5, 6]})
        current_date += timedelta(days=1)
    return dict(sorted(data.items(), key=lambda x: x[0]))


async def run() -> None:
    today = datetime.now()
    data = await fetch_workday(today.year)
    file_path = Path("data.json")
    if os.path.exists(file_path) and len(data) == 0:
        return
    lock = FileLock(f"{file_path}.lock")
    with lock:
        with open(file_path, "w+", encoding="utf-8") as fp:
            json.dump(data, fp, separators=(",", ":"))


if __name__ == "__main__":
    asyncio.run(run())
