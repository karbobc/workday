#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import uvicorn
from typing import NoReturn


def run() -> NoReturn:
    uvicorn.run("workday.app:app", port=8080, log_level="info", reload=True)
