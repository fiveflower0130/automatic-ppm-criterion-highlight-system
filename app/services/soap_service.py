import requests
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from app.config import Config

class SOAPService:
    def __init__(self, soap_url: str = Config.SOAP_URL, headers: Optional[Dict[str, str]] = None):
        self.__soap_url = soap_url
        self.__headers = headers or {'Content-Type': 'text/xml;charset=UTF-8'}

    def _build_soap_body(self, method: str, payload: Dict[str, Any]) -> str:
        """建立 SOAP 請求的 XML Body"""
        json_params = json.dumps(payload)
        return f'''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <{method} xmlns="http://tempuri.org/">
                        <EAP_Json>{json_params}</EAP_Json>
                    </{method}>
                </soap:Body>
            </soap:Envelope>
        '''

    def _parse_soap_response(self, response: requests.Response, result_tag: str) -> Dict[str, Any]:
        """解析 SOAP 響應"""
        try:
            root = ET.fromstring(response.content)
            xml_result = root.find(f'.//{{http://tempuri.org/}}{result_tag}').text
            return json.loads(xml_result)
        except Exception as err:
            raise ValueError(f"SOAP 響應解析失敗: {err}")

    def call_soap_method(self, payload: Dict[str, Any], method: str = "GetSpecValue", result_tag: str="GetSpecValueResult") -> Dict[str, Any]:
        """呼叫 SOAP 方法並回傳結果"""
        try:
            body = self._build_soap_body(method, payload)
            response = requests.post(self.__soap_url, data=body.encode('utf-8'), headers=self.__headers)
            response.raise_for_status()  # 檢查 HTTP 狀態碼
            return self._parse_soap_response(response, result_tag)
        except requests.RequestException as req_err:
            raise ConnectionError(f"SOAP API 呼叫失敗: {req_err}")
        except ValueError as parse_err:
            raise ValueError(f"SOAP 響應解析失敗: {parse_err}")