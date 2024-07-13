#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging
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

from . import fetch
from .scheduler import scheduler

data = {}
log = logging.getLogger("uvicorn")


class ApiResult(BaseModel):
    code: str = str(status.HTTP_200_OK)
    success: bool = True
    message: str = "OK"
    data: Any | None = None

    @staticmethod
    def ok(data: Any | None = None) -> Response:
        result = ApiResult(data=data)
        return Response(
            content=result.model_dump_json(exclude_none=True),
            status_code=status.HTTP_200_OK,
        )

    @staticmethod
    def e(status_code: int, message: str):
        result = ApiResult(
            code=str(status_code),
            success=False,
            message=message,
        )
        return Response(
            content=result.model_dump_json(exclude_none=True),
            status_code=status_code,
        )


class FetchDataEventHandler(PatternMatchingEventHandler):
    def on_created(self, event: FileSystemEvent) -> NoReturn:
        path = Path(event.src_path)
        log.info(f"file creation detected: {path}")
        if path.name != "data.json":
            return
        self.load_data(path)

    def on_modified(self, event: FileSystemEvent) -> NoReturn:
        path = Path(event.src_path)
        log.info(f"file modification detected: {path}")
        if path.name != "data.json":
            return
        self.load_data(path)

    @staticmethod
    def load_data(path: Path) -> NoReturn:
        lock = FileLock(f"{path}.lock")
        with lock:
            with open(path, encoding="utf-8") as fp:
                global data
                data = json.load(fp)


@asynccontextmanager
async def lifespan(app: FastAPI) -> NoReturn:
    observer = Observer()
    event_handler = FetchDataEventHandler(patterns=["*.json"], ignore_directories=True, case_sensitive=True)
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    await fetch.run()
    scheduler.start()
    log.info("scheduler start")
    yield
    observer.stop()
    scheduler.shutdown()
    log.info("scheduler end")


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception) -> Response:
    return ApiResult.e(status.HTTP_500_INTERNAL_SERVER_ERROR, f"internal server error: {repr(e)}")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, e: StarletteHTTPException) -> Response:
    return ApiResult.e(e.status_code, e.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, e: RequestValidationError) -> Response:
    return ApiResult.e(status.HTTP_400_BAD_REQUEST, f"incorrect request parameter: {e.errors()}")


@app.get("/api/workday/today")
def workday_today() -> Response:
    today = datetime.now()
    return ApiResult.ok(data={"isWorkday": data[today.strftime("%Y-%m-%d")]})


@app.get("/api/workday/{year}/{month}/{day}")
def workday(year: int, month: int, day: int) -> Response:
    try:
        return ApiResult.ok(data={"isWorkday": data[f"{year}-{month:02}-{day:02}"]})
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="incorrect date")
