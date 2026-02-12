import pytest
from unittest.mock import patch
from app.config import Config

class TestConfig:
    """設定檔測試類別"""
    
    def test_config_has_required_attributes(self):
        """測試 Config 包含必要的屬性"""
        required_attrs = [
            'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DB',
            'MSSQL_USER', 'MSSQL_PASSWORD', 'MSSQL_HOST', 'MSSQL_PORT', 'MSSQL_DB',
            'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD',
            'EMAIL_HOST', 'EMAIL_PORT',
            'BACKUP_REMOTE_PATH', 'BACKUP_DEST_PATH',
            'AI_SERVICE_HOST', 'AI_SERVICE_PORT'
        ]
        
        for attr in required_attrs:
            assert hasattr(Config, attr), f"Config 缺少屬性: {attr}"
    
    @patch.dict('os.environ', {
        'MYSQL_HOST': 'test_host',
        'MYSQL_PORT': '3307',
        'MYSQL_USER': 'test_user'
    })
    def test_config_reads_from_environment(self):
        """測試 Config 從環境變數讀取"""
        # 重新載入 Config
        from importlib import reload
        import app.config
        reload(app.config)
        
        assert app.config.Config.MYSQL_HOST == 'test_host'
        assert app.config.Config.MYSQL_PORT == '3307'
        assert app.config.Config.MYSQL_USER == 'test_user'
    
    def test_mysql_connection_string_format(self):
        """測試 MySQL 連線字串格式"""
        connection_string = (
            f"mysql+aiomysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}"
            f"@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"
        )
        
        assert "mysql+aiomysql://" in connection_string
        assert f"@{Config.MYSQL_HOST}" in connection_string
    
    def test_mssql_connection_string_format(self):
        """測試 MSSQL 連線字串格式"""
        connection_string = (
            f"mssql+aioodbc://{Config.MSSQL_USER}:{Config.MSSQL_PASSWORD}"
            f"@{Config.MSSQL_HOST}:{Config.MSSQL_PORT}/{Config.MSSQL_DB}"
        )
        
        assert "mssql+aioodbc://" in connection_string
        assert f"@{Config.MSSQL_HOST}" in connection_string
    
    def test_redis_connection_format(self):
        """測試 Redis 連線格式"""
        redis_url = f"redis://:{Config.REDIS_PASSWORD}@{Config.REDIS_HOST}:{Config.REDIS_PORT}"
        
        assert "redis://" in redis_url
        assert f"@{Config.REDIS_HOST}" in redis_url
    
    def test_backup_paths_are_valid(self):
        """測試備份路徑設定有效"""
        assert Config.BACKUP_REMOTE_PATH is not None
        assert Config.BACKUP_DEST_PATH is not None
        assert len(Config.BACKUP_REMOTE_PATH) > 0
        assert len(Config.BACKUP_DEST_PATH) > 0


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])