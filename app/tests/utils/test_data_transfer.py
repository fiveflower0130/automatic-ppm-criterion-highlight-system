import pytest
from unittest.mock import patch, MagicMock
from app.utils.data_transfer import DataTransfer

class TestDataTransfer:
    """資料轉換工具測試類別"""
    
    @pytest.fixture
    def data_transfer(self):
        """建立 DataTransfer 實例"""
        return DataTransfer()
    
    def test_data_transfer_singleton(self):
        """測試 DataTransfer 單例模式"""
        instance1 = DataTransfer()
        instance2 = DataTransfer()
        assert instance1 is instance2
    
    @patch('pandas.read_excel')
    def test_read_excel_success(self, mock_read_excel, data_transfer):
        """測試成功讀取 Excel 檔案"""
        mock_df = MagicMock()
        mock_read_excel.return_value = mock_df
        
        result = data_transfer._DataTransfer__read_excel("test.xlsx", "Sheet1", [0, 1])
        
        assert result == mock_df
        mock_read_excel.assert_called_once_with("test.xlsx", sheet_name="Sheet1", usecols=[0, 1])
    
    def test_get_failrate_count(self, data_transfer):
        """測試計算失效率"""
        mock_data = {
            "machine1": [
                MagicMock(judge_ppm=1),
                MagicMock(judge_ppm=0),
                MagicMock(judge_ppm=1),
                MagicMock(judge_ppm=0)
            ]
        }
        
        result = data_transfer._DataTransfer__get_failrate_count(mock_data)
        
        assert result["machine1"]["total_count"] == 4
        assert result["machine1"]["fail_count"] == 2
        assert result["machine1"]["fail_rate"] == 0.5