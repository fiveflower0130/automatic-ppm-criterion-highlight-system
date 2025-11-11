import pytest
from app.models.mysql_models import DrillInfo, MailInfo, PPMCriteriaLimitInfo

class TestMySQLModels:
    """MySQL 模型測試類別"""
    
    def test_drill_info_model(self):
        """測試 DrillInfo 模型"""
        # 測試模型屬性存在
        assert hasattr(DrillInfo, '__tablename__')
        assert hasattr(DrillInfo, 'id')
        assert hasattr(DrillInfo, 'lot_number')
        assert hasattr(DrillInfo, 'drill_machine_name')
    
    def test_mail_info_model(self):
        """測試 MailInfo 模型"""
        assert hasattr(MailInfo, '__tablename__')
        assert hasattr(MailInfo, 'id')
        assert hasattr(MailInfo, 'email')
    
    def test_ppm_criteria_limit_info_model(self):
        """測試 PPMCriteriaLimitInfo 模型"""
        assert hasattr(PPMCriteriaLimitInfo, '__tablename__')
        assert hasattr(PPMCriteriaLimitInfo, 'id')
        assert hasattr(PPMCriteriaLimitInfo, 'product_name')