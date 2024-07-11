#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging

import uvicorn

from .app import app


def run() -> None:
    uvicorn.run(app, port=8080, log_level=logging.INFO)
