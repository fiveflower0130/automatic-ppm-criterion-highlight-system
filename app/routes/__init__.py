# -*- coding: utf-8 -*-
"""
app/routes/__init__.py
Routes 模組初始化
"""
from .drill import router as drill_router
from .feedback import router as feedback_router
from .mail import router as mail_router
from .ppm import router as ppm_router
from .user import router as user_router

__all__ = ["drill_router", "feedback_router", "mail_router", "ppm_router", "user_router"]