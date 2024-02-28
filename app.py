#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import time
import fetch
from datetime import datetime
from pydantic import BaseModel
from scheduler import scheduler
from typing import Any, NoReturn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import HTTPException, RequestValidationError, StarletteHTTPException

data = {}


class ApiResult(BaseModel):
    code: str = str(status.HTTP_200_OK)
    success: bool = True
    timestamp: str = str(int(time.time() * 1000))
    message: str = "OK"
    data: Any | None = None


async def startup_event() -> None:
    await fetch.run()
    with open("data.json", "r", encoding="utf-8") as fp:
        global data
        data = json.load(fp)
    scheduler.start()
    print("scheduler start")


async def shutdown_event() -> None:
    scheduler.shutdown()
    print("scheduler end")


@asynccontextmanager
async def lifespan(app: FastAPI) -> NoReturn:
    await startup_event()
    yield
    await shutdown_event()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception) -> Response:
    result = ApiResult(code=str(status.HTTP_500_INTERNAL_SERVER_ERROR), success=False, message=f"internal server error: {repr(e)}")
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, e: StarletteHTTPException) -> Response:
    result = ApiResult(code=str(e.status_code), success=False, message=e.detail)
    return Response(
        content=result.model_dump_json(exclude_none=True),
        status_code=e.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, e: RequestValidationError) -> Response:
    result = ApiResult(code=str(status.HTTP_404_NOT_FOUND), success=False, message="incorrect request parameter")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="incorrect date")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", port=8080, log_level="info", reload=True)
