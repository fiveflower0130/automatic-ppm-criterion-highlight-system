import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tqm_service import TQMProcessor, TQMProcessorConfig

class TestTQMProcessorConfig:
    """TQM 處理器設定測試類別"""
    
    def test_tqm_processor_config_creation(self):
        """測試 TQMProcessorConfig 建立"""
        config = TQMProcessorConfig(
            max_db_workers=5,
            batch_size=500,
            enable_email=True,
            enable_save=True
        )
        
        assert config.max_db_workers == 5
        assert config.batch_size == 500
        assert config.enable_email == True
        assert config.enable_save == True


class TestTQMProcessor:
    """TQM 處理器測試類別"""
    
    @pytest.fixture
    def tqm_config(self):
        """建立 TQM 設定"""
        return TQMProcessorConfig(
            max_db_workers=5,
            batch_size=500,
            enable_email=False,
            enable_save=True
        )
    
    @pytest.fixture
    def mock_email_client(self):
        """模擬電子郵件客戶端"""
        return MagicMock()
    
    @pytest.fixture
    def mock_data_transfer(self):
        """模擬資料轉換器"""
        transfer = MagicMock()
        transfer.get_ppm_ar_value.return_value = {"ColumnValue_1": 1.5}
        return transfer
    
    @pytest.fixture
    def tqm_processor(self, tqm_config, mock_email_client, mock_data_transfer):
        """建立 TQMProcessor 實例"""
        return TQMProcessor(
            work_config=tqm_config,
            data_transfer=mock_data_transfer,
            email_client=mock_email_client,
            email_host="smtp.test.com"
        )
    
    def test_tqm_processor_init(self, tqm_processor, tqm_config):
        """測試 TQMProcessor 初始化"""
        assert tqm_processor.work_config == tqm_config
        assert tqm_processor.email_host == "smtp.test.com"
    
    @pytest.mark.asyncio
    @patch('app.crud.tqm.get_board_by_last_aoi_time')
    @patch('app.crud.drill.get_drill_info_by_last_aoitime')
    async def test_get_last_process_time_success(
        self, mock_get_drill_info, mock_get_board, tqm_processor
    ):
        """測試成功取得最後處理時間"""
        # 模擬資料庫回應
        mock_drill_record = MagicMock()
        mock_drill_record.aoi_time = datetime.datetime(2025, 1, 1, 10, 0, 0)
        mock_get_drill_info.return_value = mock_drill_record
        
        mock_mssql_session = AsyncMock()
        mock_mysql_session = AsyncMock()
        
        result = await tqm_processor._TQMProcessor__get_last_process_time(
            mock_mssql_session, mock_mysql_session
        )
        
        assert isinstance(result, datetime.datetime)
        mock_get_drill_info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.crud.tqm.get_board_by_last_aoi_time')
    @patch('app.crud.drill.get_drill_info_by_last_aoitime')
    async def test_get_last_process_time_no_records(
        self, mock_get_drill_info, mock_get_board, tqm_processor
    ):
        """測試無記錄時的預設時間"""
        mock_get_drill_info.return_value = None
        mock_get_board.return_value = None
        
        mock_mssql_session = AsyncMock()
        mock_mysql_session = AsyncMock()
        
        result = await tqm_processor._TQMProcessor__get_last_process_time(
            mock_mssql_session, mock_mysql_session
        )
        
        # 應該回傳預設時間（2024-01-01）
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
    
    @pytest.mark.asyncio
    @patch('app.crud.tqm.get_board_data')
    async def test_get_board_data_success(self, mock_get_board_data, tqm_processor):
        """測試成功取得 Board 資料"""
        mock_boards = [
            MagicMock(ID_B=1, ProductID=1, DrillMachineID=1),
            MagicMock(ID_B=2, ProductID=2, DrillMachineID=2)
        ]
        mock_get_board_data.return_value = mock_boards
        
        mock_session = AsyncMock()
        start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
        
        result = await tqm_processor._TQMProcessor__get_board_data(
            mock_session, start_time
        )
        
        assert len(result) == 2
        mock_get_board_data.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.crud.drill.create_drill_info')
    async def test_save_drill_info_success(self, mock_create_drill, tqm_processor):
        """測試成功儲存 DrillInfo"""
        mock_drill_data = [
            MagicMock(lot_number="L001", drill_machine_name="ND01"),
            MagicMock(lot_number="L002", drill_machine_name="ND02")
        ]
        
        mock_session = AsyncMock()
        mock_create_drill.return_value = None
        
        await tqm_processor._TQMProcessor__save_drill_info(
            mock_session, mock_drill_data
        )
        
        assert mock_create_drill.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.prediction_service.get_ai_classification')
    async def test_get_ai_prediction_success(self, mock_get_ai, tqm_processor):
        """測試成功取得 AI 預測"""
        mock_get_ai.return_value = {
            "classification_code": "OK",
            "classification_model": "test_model",
            "distance": 0.5
        }
        
        result = await tqm_processor._TQMProcessor__get_ai_prediction(
            "test_image.jpg", "test_product"
        )
        
        assert result["classification_code"] == "OK"
        mock_get_ai.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.crud.ppm.get_ppm_criteria_limit')
    @patch('app.crud.ppm.create_ppm_criteria_limit')
    async def test_check_and_create_ppm_criteria(
        self, mock_create_ppm, mock_get_ppm, tqm_processor
    ):
        """測試檢查並建立 PPM 標準"""
        mock_get_ppm.return_value = None  # 不存在
        mock_create_ppm.return_value = None
        
        mock_session = AsyncMock()
        product_info = {"product_name": "TEST_PRODUCT", "ar_value": 1.5}
        
        await tqm_processor._TQMProcessor__check_and_create_ppm_criteria(
            mock_session, product_info
        )
        
        mock_get_ppm.assert_called_once()
        mock_create_ppm.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.crud.mail.get_mail_list')
    async def test_send_warning_email_when_enabled(
        self, mock_get_mail_list, tqm_processor
    ):
        """測試啟用時發送警告郵件"""
        tqm_processor.work_config.enable_email = True
        
        mock_mail_list = [
            MagicMock(email="test1@test.com", mail_to_cc_bcc="to"),
            MagicMock(email="test2@test.com", mail_to_cc_bcc="cc")
        ]
        mock_get_mail_list.return_value = mock_mail_list
        
        mock_session = AsyncMock()
        highlight_info = {
            "machine_name": "ND01",
            "lot_number": "L001",
            "spindle_id": 1,
            "ppm": 1500
        }
        
        with patch.object(tqm_processor.email_client, 'send_email') as mock_send:
            await tqm_processor._TQMProcessor__send_warning_email(
                mock_session, highlight_info
            )
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.crud.mail.get_mail_list')
    async def test_send_warning_email_when_disabled(
        self, mock_get_mail_list, tqm_processor
    ):
        """測試停用時不發送郵件"""
        tqm_processor.work_config.enable_email = False
        
        mock_session = AsyncMock()
        highlight_info = {"machine_name": "ND01"}
        
        with patch.object(tqm_processor.email_client, 'send_email') as mock_send:
            await tqm_processor._TQMProcessor__send_warning_email(
                mock_session, highlight_info
            )
            
            mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.database.mssql_session')
    @patch('app.database.mysql_session')
    @patch('asyncio.to_thread')
    async def test_run_process_success(
        self, mock_to_thread, mock_mysql_session, mock_mssql_session, tqm_processor
    ):
        """測試成功執行完整處理流程"""
        # 模擬資料庫 session
        mock_mssql_db = AsyncMock()
        mock_mysql_db = AsyncMock()
        mock_mssql_session.return_value.__aenter__.return_value = mock_mssql_db
        mock_mysql_session.return_value.__aenter__.return_value = mock_mysql_db
        
        # 模擬處理時間
        with patch.object(
            tqm_processor, '_TQMProcessor__get_last_process_time',
            return_value=datetime.datetime(2025, 1, 1, 0, 0, 0)
        ):
            # 模擬 Board 資料
            with patch.object(
                tqm_processor, '_TQMProcessor__get_board_data',
                return_value=[]
            ):
                await tqm_processor.run_process()
        
        # 驗證資料庫 session 被正確使用
        mock_mssql_session.assert_called()
        mock_mysql_session.assert_called()
    
    @pytest.mark.asyncio
    async def test_run_process_exception_handling(self, tqm_processor):
        """測試處理流程異常處理"""
        with patch('app.database.mssql_session') as mock_mssql:
            mock_mssql.side_effect = Exception("Database error")
            
            # 不應該拋出異常
            await tqm_processor.run_process()


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])