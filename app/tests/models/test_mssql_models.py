import pytest
from app.models.mssql_models import BoardInfo, MeasureInfo, ProductInfo, MachineInfo

class TestMSSQLModels:
    """MSSQL 模型測試類別"""
    
    def test_board_info_model(self):
        """測試 BoardInfo 模型"""
        assert hasattr(BoardInfo, '__tablename__')
        assert hasattr(BoardInfo, 'ID_B')
        assert hasattr(BoardInfo, 'ProductID')
        assert hasattr(BoardInfo, 'DrillMachineID')
    
    def test_measure_info_model(self):
        """測試 MeasureInfo 模型"""
        assert hasattr(MeasureInfo, '__tablename__')
        
    def test_product_info_model(self):
        """測試 ProductInfo 模型"""
        assert hasattr(ProductInfo, '__tablename__')
        
    def test_machine_info_model(self):
        """測試 MachineInfo 模型"""
        assert hasattr(MachineInfo, '__tablename__')