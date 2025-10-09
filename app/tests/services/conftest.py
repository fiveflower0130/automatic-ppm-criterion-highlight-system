# -*- coding: utf-8 -*-
"""
# app/tests/services/conftest.py
Services 測試專用 fixtures
"""

import pytest
from unittest.mock import MagicMock
from app.services.backup_service import BackupProcessorConfig

@pytest.fixture
def backup_config():
    """備份處理器設定 fixture"""
    return BackupProcessorConfig(
        remote_path=r"\\test-server\shared",
        dest_path=r"D:\test_backup",
        username="test_user",
        password="test_pass",
        domain="test_domain",
        retry=3
    )

@pytest.fixture
def mock_remote_connector():
    """模擬遠端連線器"""
    connector = MagicMock()
    connector.connect.return_value = True
    connector.connected = True
    connector.disconnect = MagicMock()
    return connector