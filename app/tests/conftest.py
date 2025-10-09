# -*- coding: utf-8 -*-
"""
# app/tests/conftest.py
pytest 共用設定和 fixtures
這個檔案會被 pytest 自動載入，提供給所有測試模組使用
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture(scope="session")
def event_loop():
    """建立事件迴圈 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_mysql_session():
    """模擬 MySQL 資料庫 session"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_logger():
    """模擬 Logger"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger

@pytest.fixture
def mock_email_client():
    """模擬 Email 客戶端"""
    client = MagicMock()
    client.add_client = MagicMock()
    client.send_email = MagicMock()
    client.delete_client = MagicMock()
    return client

@pytest.fixture
def mock_data_transfer():
    """模擬 DataTransfer"""
    transfer = MagicMock()
    transfer.get_ppm_ar_value = MagicMock(return_value={"ColumnValue_1": 1.5})
    transfer.validate_datetime_format = MagicMock(return_value=True)
    transfer.get_image_file_check = MagicMock(return_value=True)
    return transfer

@pytest.fixture
def mock_config():
    """模擬設定"""
    config = MagicMock()
    config.MYSQL_HOST = "localhost"
    config.MYSQL_PORT = "3306"
    config.MYSQL_USER = "test_user"
    config.MYSQL_PASSWORD = "test_pass"
    config.MYSQL_DB = "test_db"
    return config