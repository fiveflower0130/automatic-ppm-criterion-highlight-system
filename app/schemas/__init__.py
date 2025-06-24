# -*- coding: utf-8 -*-
"""
# app/schemas/__init__.py
Schemas 模組初始化
"""
from .drill import DrillInfo, SearchDrill, SearchFailrate, DrillReport, ReportUpdate
from .feedback import SearchFeedback, DrillFeedback, FeedbackRecord
from .ppm import PPMCriteriaLimitInfo, PPMARLimitInfo
from .mail import MailInfo, EEInfo
from .user import UserModificationRecord
from .predcition import PredictionRecord