import pytest
from unittest.mock import patch, MagicMock
from app.services.soap_service import SOAPService

class TestSOAPService:
    """SOAP 服務測試類別"""
    
    @pytest.fixture
    def soap_service(self):
        """建立 SOAPService 實例"""
        return SOAPService("http://test.soap.com/service.asmx")
    
    def test_soap_service_init(self, soap_service):
        """測試 SOAPService 初始化"""
        assert soap_service._SOAPService__soap_url == "http://test.soap.com/service.asmx"
        assert 'Content-Type' in soap_service._SOAPService__headers
    
    def test_build_soap_body(self, soap_service):
        """測試建立 SOAP 請求主體"""
        payload = {"test": "value"}
        result = soap_service._build_soap_body("TestMethod", payload)
        
        assert "TestMethod" in result
        assert '"test": "value"' in result
        assert "soap:Envelope" in result
    
    @patch('requests.post')
    def test_call_soap_method_success(self, mock_post, soap_service):
        """測試成功呼叫 SOAP 方法"""
        # 模擬回應
        mock_response = MagicMock()
        mock_response.content = b'''<?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <TestMethodResult xmlns="http://tempuri.org/">{"result": "success"}</TestMethodResult>
            </soap:Body>
        </soap:Envelope>'''
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = soap_service.call_soap_method({"test": "value"}, "TestMethod", "TestMethodResult")
        
        assert result == {"result": "success"}
        mock_post.assert_called_once()