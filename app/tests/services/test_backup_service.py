import pytest
import asyncio
import os
import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from dataclasses import dataclass
from app.services.backup_service import (
    RemoteFolderConnector, 
    BackupProcessorConfig, 
    BackupProcessor
)

class TestRemoteFolderConnector:
    """遠端資料夾連線器測試類別"""
    
    @pytest.fixture
    def connector_config(self):
        """建立連線設定"""
        return {
            "remote_path": r"\\test-server\shared",
            "username": "test_user",
            "password": "test_pass",
            "domain": "test_domain",
            "retry": 3
        }
    
    @pytest.fixture
    def connector(self, connector_config):
        """建立 RemoteFolderConnector 實例"""
        return RemoteFolderConnector(**connector_config)
    
    def test_remote_folder_connector_init(self, connector, connector_config):
        """測試 RemoteFolderConnector 初始化"""
        assert connector._remote_path == connector_config["remote_path"]
        assert connector._username == connector_config["username"]
        assert connector._password == connector_config["password"]
        assert connector._domain == connector_config["domain"]
        assert connector._retry == connector_config["retry"]
        assert connector.connected == False
    
    @patch('win32wnet.WNetAddConnection2')
    @patch('win32wnet.NETRESOURCE')
    def test_connect_success(self, mock_netresource, mock_wnet_add, connector):
        """測試成功連線到遠端資料夾"""
        # 模擬成功連線
        mock_wnet_add.return_value = None
        
        result = connector.connect()
        
        assert result == True
        assert connector.connected == True
        mock_wnet_add.assert_called_once()
    
    @patch('win32wnet.WNetAddConnection2')
    @patch('win32wnet.NETRESOURCE')
    def test_connect_failure_after_retries(self, mock_netresource, mock_wnet_add, connector):
        """測試連線失敗且重試後仍失敗"""
        # 模擬連線失敗
        mock_wnet_add.side_effect = Exception("Connection failed")
        
        result = connector.connect()
        
        assert result == False
        assert connector.connected == False
        assert mock_wnet_add.call_count == 3  # 重試 3 次
    
    @patch('win32wnet.WNetCancelConnection2')
    def test_disconnect_success(self, mock_wnet_cancel, connector):
        """測試成功斷開連線"""
        connector.connected = True
        
        connector.disconnect()
        
        assert connector.connected == False
        mock_wnet_cancel.assert_called_once_with(connector._remote_path, 0, True)
    
    @patch('win32wnet.WNetCancelConnection2')
    def test_disconnect_with_error(self, mock_wnet_cancel, connector):
        """測試斷開連線時發生錯誤"""
        connector.connected = True
        mock_wnet_cancel.side_effect = Exception("Disconnect failed")
        
        # 不應該拋出異常
        connector.disconnect()
        
        mock_wnet_cancel.assert_called_once()


class TestBackupProcessorConfig:
    """備份處理器設定測試類別"""
    
    def test_backup_processor_config_creation(self):
        """測試 BackupProcessorConfig 建立"""
        config = BackupProcessorConfig(
            remote_path=r"\\test-server\shared",
            dest_path=r"D:\backup",
            username="test_user",
            password="test_pass",
            domain="test_domain",
            retry=3
        )
        
        assert config.remote_path == r"\\test-server\shared"
        assert config.dest_path == r"D:\backup"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.domain == "test_domain"
        assert config.retry == 3


class TestBackupProcessor:
    """備份資料處理器測試類別"""
    
    @pytest.fixture
    def backup_config(self):
        """建立備份設定"""
        return BackupProcessorConfig(
            remote_path=r"\\test-server\shared",
            dest_path=r"D:\backup",
            username="test_user",
            password="test_pass",
            domain="test_domain",
            retry=3
        )
    
    @pytest.fixture
    def mock_email_client(self):
        """模擬電子郵件客戶端"""
        return MagicMock()
    
    @pytest.fixture
    def backup_processor(self, backup_config, mock_email_client):
        """建立 BackupProcessor 實例"""
        return BackupProcessor(
            connection_config=backup_config,
            email_client=mock_email_client,
            email_host="smtp.test.com"
        )
    
    def test_backup_processor_init(self, backup_processor, backup_config, mock_email_client):
        """測試 BackupProcessor 初始化"""
        assert backup_processor.connection_config == backup_config
        assert backup_processor.email_client == mock_email_client
        assert backup_processor.email_host == "smtp.test.com"
        assert backup_processor.pending_list == []
        assert backup_processor._BackupProcessor__file_count == 0
        assert backup_processor._BackupProcessor__copied_count == 0
        assert backup_processor._BackupProcessor__db_updated_count == 0
    
    def test_parse_filename_valid_target(self, backup_processor):
        """測試解析有效的 Target 檔案名稱"""
        filename = "20250917025100ND08SP6L250910079Target.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result["image_create_time"] == "2025-09-17 02:51:00"
        assert result["machine_name"] == "ND08"
        assert result["spindle_id"] == "6"
        assert result["lot_number"] == "L250910079"
        assert result["target_panel"] == "Target"
    
    def test_parse_filename_valid_panel(self, backup_processor):
        """測試解析有效的 Panel 檔案名稱"""
        filename = "20250917025100ND08SP6L250910079Panel.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result["image_create_time"] == "2025-09-17 02:51:00"
        assert result["machine_name"] == "ND08"
        assert result["spindle_id"] == "6"
        assert result["lot_number"] == "L250910079"
        assert result["target_panel"] == "Panel"
    
    def test_parse_filename_invalid_format(self, backup_processor):
        """測試解析無效格式的檔案名稱"""
        filename = "invalid_filename.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result == {}
    
    def test_parse_filename_too_short(self, backup_processor):
        """測試解析太短的檔案名稱"""
        filename = "short.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result == {}
    
    def test_parse_filename_invalid_ending(self, backup_processor):
        """測試解析無效結尾的檔案名稱"""
        filename = "20250917025100ND08SP6L250910079Invalid.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result == {}
    
    @patch('app.services.backup_service.logger')
    def test_parse_filename_exception(self, mock_logger, backup_processor):
        """測試解析檔案名稱時發生異常"""
        # 使用會導致 strptime 失敗的檔案名稱
        filename = "invalid_dateND08SP6L250910079Target.jpg"
        
        result = backup_processor._BackupProcessor__parse_filename(filename)
        
        assert result == {}
        mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    @patch('os.makedirs')
    @patch('os.walk')
    @patch('os.path.exists')
    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('os.remove')
    @patch('app.database.mysql_session')
    @patch('app.crud.drill.get_drill_info_by_image_info')
    @patch('app.crud.drill.update_drill_report_info')
    async def test_run_process_success(
        self, mock_update_drill, mock_get_drill_info, mock_mysql_session,
        mock_remove, mock_getmtime, mock_copy2, mock_exists, mock_walk,
        mock_makedirs, mock_to_thread, backup_processor
    ):
        """測試成功執行備份流程"""
        # 模擬連線成功
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.connected = True
        mock_to_thread.side_effect = [True, None]  # connect, disconnect
        
        # 模擬檔案系統
        mock_walk.return_value = [
            (r"\\test-server\shared\machine1", [], ["20250917025100ND08SP6L250910079Target.jpg"])
        ]
        mock_exists.return_value = False  # 檔案不存在，需要複製
        mock_getmtime.return_value = 1695772260.0  # 固定時間戳
        
        # 模擬資料庫
        mock_db_session = AsyncMock()
        mock_mysql_session.return_value.__aenter__.return_value = mock_db_session
        
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.lot_number = "L250910079"
        mock_record.drill_machine_id = 1
        mock_record.drill_spindle_id = 5
        mock_record.aoi_time = datetime.datetime.now()
        mock_record.image_path = None
        mock_record.image_update_time = None
        
        mock_get_drill_info.return_value = [mock_record]
        mock_update_drill.return_value = True
        
        # 修補 RemoteFolderConnector
        with patch('app.services.backup_service.RemoteFolderConnector', return_value=mock_connector):
            await backup_processor.run_process()
        
        # 驗證呼叫
        mock_makedirs.assert_called()
        mock_copy2.assert_called()
        mock_get_drill_info.assert_called()
        mock_update_drill.assert_called()
        
        # 驗證計數器
        assert backup_processor._BackupProcessor__file_count == 1
        assert backup_processor._BackupProcessor__copied_count == 1
        assert backup_processor._BackupProcessor__db_updated_count == 1
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    @patch('os.makedirs')
    async def test_run_process_connection_failure(self, mock_makedirs, mock_to_thread, backup_processor):
        """測試連線失敗的情況"""
        # 模擬連線失敗
        mock_connector = MagicMock()
        mock_connector.connect.return_value = False
        mock_connector.connected = False
        mock_to_thread.side_effect = [False]  # connect fails
        
        with patch('app.services.backup_service.RemoteFolderConnector', return_value=mock_connector):
            await backup_processor.run_process()
        
        # 驗證只呼叫了 makedirs，其他操作都沒有執行
        mock_makedirs.assert_called_once()
        assert backup_processor._BackupProcessor__file_count == 0
        assert backup_processor._BackupProcessor__copied_count == 0
        assert backup_processor._BackupProcessor__db_updated_count == 0
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    @patch('os.makedirs')
    @patch('os.walk')
    @patch('os.path.exists')
    @patch('shutil.copy2')
    @patch('os.remove')
    @patch('app.database.mysql_session')
    @patch('app.crud.drill.get_drill_info_by_image_info')
    async def test_run_process_no_matching_record(
        self, mock_get_drill_info, mock_mysql_session, mock_remove,
        mock_copy2, mock_exists, mock_walk, mock_makedirs, mock_to_thread,
        backup_processor
    ):
        """測試沒有找到匹配記錄的情況"""
        # 模擬連線成功
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.connected = True
        mock_to_thread.side_effect = [True, None]
        
        # 模擬檔案系統
        mock_walk.return_value = [
            (r"\\test-server\shared\machine1", [], ["20250917025100ND08SP6L250910079Target.jpg"])
        ]
        mock_exists.return_value = False
        
        # 模擬資料庫
        mock_db_session = AsyncMock()
        mock_mysql_session.return_value.__aenter__.return_value = mock_db_session
        mock_get_drill_info.return_value = []  # 沒有找到記錄
        
        with patch('app.services.backup_service.RemoteFolderConnector', return_value=mock_connector):
            await backup_processor.run_process()
        
        # 驗證檔案被複製然後刪除
        mock_copy2.assert_called()
        mock_remove.assert_called()
        assert backup_processor._BackupProcessor__copied_count == 0  # 複製後被刪除，所以是 0
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    @patch('os.makedirs')
    @patch('os.walk')
    @patch('os.path.exists')
    @patch('shutil.copy2')
    @patch('app.database.mysql_session')
    @patch('app.crud.drill.get_drill_info_by_image_info')
    async def test_run_process_skip_panel_files(
        self, mock_get_drill_info, mock_mysql_session, mock_copy2,
        mock_exists, mock_walk, mock_makedirs, mock_to_thread, backup_processor
    ):
        """測試跳過 Panel 檔案的情況"""
        # 模擬連線成功
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.connected = True
        mock_to_thread.side_effect = [True, None]
        
        # 模擬檔案系統 - Panel 檔案
        mock_walk.return_value = [
            (r"\\test-server\shared\machine1", [], ["20250917025100ND08SP6L250910079Panel.jpg"])
        ]
        mock_exists.return_value = False
        
        # 模擬資料庫
        mock_db_session = AsyncMock()
        mock_mysql_session.return_value.__aenter__.return_value = mock_db_session
        
        with patch('app.services.backup_service.RemoteFolderConnector', return_value=mock_connector):
            await backup_processor.run_process()
        
        # 驗證 Panel 檔案被複製但不會查詢資料庫
        mock_copy2.assert_called()
        mock_get_drill_info.assert_not_called()
        assert backup_processor._BackupProcessor__file_count == 1
        assert backup_processor._BackupProcessor__copied_count == 1
        assert backup_processor._BackupProcessor__db_updated_count == 0
    
    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    @patch('os.makedirs')
    @patch('os.walk')
    @patch('os.path.exists')
    @patch('shutil.copy2')
    @patch('os.path.getmtime')
    @patch('app.database.mysql_session')
    @patch('app.crud.drill.get_drill_info_by_image_info')
    @patch('app.crud.drill.update_drill_report_info')
    async def test_run_process_update_failure_adds_to_pending(
        self, mock_update_drill, mock_get_drill_info, mock_mysql_session,
        mock_getmtime, mock_copy2, mock_exists, mock_walk, mock_makedirs,
        mock_to_thread, backup_processor
    ):
        """測試更新失敗時加入待處理清單"""
        # 模擬連線成功
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_connector.connected = True
        mock_to_thread.side_effect = [True, None]
        
        # 模擬檔案系統
        mock_walk.return_value = [
            (r"\\test-server\shared\machine1", [], ["20250917025100ND08SP6L250910079Target.jpg"])
        ]
        mock_exists.return_value = False
        mock_getmtime.return_value = 1695772260.0
        
        # 模擬資料庫
        mock_db_session = AsyncMock()
        mock_mysql_session.return_value.__aenter__.return_value = mock_db_session
        
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.lot_number = "L250910079"
        mock_record.drill_machine_id = 1
        mock_record.drill_spindle_id = 5
        mock_record.aoi_time = datetime.datetime.now()
        mock_record.image_path = None
        mock_record.image_update_time = None
        
        mock_get_drill_info.return_value = [mock_record]
        mock_update_drill.return_value = False  # 更新失敗
        
        with patch('app.services.backup_service.RemoteFolderConnector', return_value=mock_connector):
            await backup_processor.run_process()
        
        # 驗證失敗的更新被加入待處理清單
        assert len(backup_processor.pending_list) == 1
        assert backup_processor._BackupProcessor__db_updated_count == 0


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])