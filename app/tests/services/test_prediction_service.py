import pytest
from unittest.mock import patch, AsyncMock
from app.services.prediction_service import get_ai_classification

class TestPredictionService:
    """AI 預測服務測試類別"""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_ai_classification_success(self, mock_client):
        """測試成功取得 AI 分類結果"""
        # 模擬 httpx 客戶端回應
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "classification_code": "OK",
            "classification_model": "test_model",
            "distance": 0.5
        }
        mock_response.raise_for_status = AsyncMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await get_ai_classification("test_image.jpg", "test_product")
        
        assert result["classification_code"] == "OK"
        assert result["classification_model"] == "test_model"
        mock_client_instance.post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_ai_classification_error(self, mock_client):
        """測試 AI 分類服務錯誤處理"""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = Exception("Connection error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await get_ai_classification("test_image.jpg", "test_product")
        
        assert result["classification_code"] == "ERROR"
        assert "error" in result