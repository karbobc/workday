#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    StarletteHTTPException,
)
from filelock import FileLock
from pydantic import BaseModel
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from workday import fetch
from workday.scheduler import scheduler

data = {}


class ApiResult(BaseModel):
    code: str = str(status.HTTP_200_OK)
    success: bool = True
    message: str = "OK"
    data: Any | None = None


class FetchDataEventHandler(PatternMatchingEventHandler):
    def on_created(self, event: FileSystemEvent) -> NoReturn:
        path = Path(event.src_path)
        print(f"file creation detected: {path}")
        if path.name != "data.json":
            return
        self.load_data(path)

    def on_modified(self, event: FileSystemEvent) -> NoReturn:
        path = Path(event.src_path)
        print(f"file modification detected: {path}")
        if path.name != "data.json":
            return
        self.load_data(path)

    @staticmethod
    def load_data(path: Path) -> NoReturn:
        lock = FileLock(f"{path}.lock")
        with lock:
            with open(path, "r", encoding="utf-8") as fp:
                global data
                data = json.load(fp)


@asynccontextmanager
async def lifespan(app: FastAPI) -> NoReturn:
    observer = Observer()
    event_handler = FetchDataEventHandler(
        patterns=["*.json"], ignore_directories=True, case_sensitive=True
    )
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    await fetch.run()
    scheduler.start()
    print("scheduler start")
    yield
    observer.stop()
    scheduler.shutdown()
    print("scheduler end")


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception) -> Response:
    result = ApiResult(
        code=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
        success=False,
        message=f"internal server error: {repr(e)}",
    )
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, e: StarletteHTTPException
) -> Response:
    result = ApiResult(code=str(e.status_code), success=False, message=e.detail)
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=e.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, e: RequestValidationError
) -> Response:
    result = ApiResult(
        code=str(status.HTTP_404_NOT_FOUND),
        success=False,
        message="incorrect request parameter",
    )
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.get("/api/workday/today")
def workday_today() -> Response:
    today = datetime.now()
    result = ApiResult(data={"isWorkday": data[today.strftime("%Y-%m-%d")]})
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=status.HTTP_200_OK,
    )


@app.get("/api/workday/{year}/{month}/{day}")
def workday(year: int, month: int, day: int) -> Response:
    try:
        result = ApiResult(data={"isWorkday": data[f"{year}-{month:02}-{day:02}"]})
        return Response(
            content=result.model_dump_json(exclude_none=True),
            status_code=status.HTTP_200_OK,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="incorrect date"
        )
