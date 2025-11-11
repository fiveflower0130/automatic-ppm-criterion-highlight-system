import pytest
from unittest.mock import MagicMock, patch
from app.services.email_service import EmailClient

class TestEmailClient:
    """電子郵件服務測試類別"""
    
    @pytest.fixture
    def email_client(self):
        """建立 EmailClient 實例"""
        return EmailClient()
    
    def test_email_client_init(self, email_client):
        """測試 EmailClient 初始化"""
        assert hasattr(email_client, '_EmailClient__email_clients')
        assert email_client._EmailClient__email_clients == {}
    
    @patch('smtplib.SMTP')
    def test_add_client_success(self, mock_smtp, email_client):
        """測試成功新增 SMTP 客戶端"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        email_client.add_client("test.smtp.com", "587", "user", "pass")
        
        mock_smtp.assert_called_once_with("test.smtp.com:587")
        mock_smtp_instance.login.assert_called_once_with("user", "pass")
        assert "test.smtp.com" in email_client._EmailClient__email_clients
    
    def test_delete_client_success(self, email_client):
        """測試成功刪除 SMTP 客戶端"""
        mock_client = MagicMock()
        email_client._EmailClient__email_clients["test.smtp.com"] = mock_client
        
        email_client.delete_client("test.smtp.com")
        
        mock_client.quit.assert_called_once()
        assert "test.smtp.com" not in email_client._EmailClient__email_clients