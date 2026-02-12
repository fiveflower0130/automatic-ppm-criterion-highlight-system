import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import user
from app.schemas.user import UserModificationRecord
from app.models.mysql_models import UserModificationRecord as UserModificationRecordModel

class TestUserCRUD:
    """User CRUD 操作測試類別"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫 session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_get_user_modifications(self, mock_db_session):
        """測試取得使用者修改記錄"""
        mock_records = [
            MagicMock(id=1, user_name="user1", action="UPDATE"),
            MagicMock(id=2, user_name="user2", action="DELETE")
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await user.get_user_modifications(mock_db_session)
        
        assert len(result) == 2
        assert result[0].action == "UPDATE"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_modification_by_id(self, mock_db_session):
        """測試根據 ID 取得使用者修改記錄"""
        mock_record = MagicMock(id=1, user_name="test_user")
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        result = await user.get_user_modification_by_id(mock_db_session, 1)
        
        assert result.id == 1
        assert result.user_name == "test_user"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_modification_record(self, mock_db_session):
        """測試建立使用者修改記錄"""
        modification_data = UserModificationRecord(
            user_name="test_user",
            action="UPDATE",
            table_name="drill_info",
            record_id=1,
            modification_time=datetime.datetime.now(),
            description="測試修改"
        )
        
        await user.create_user_modification_record(mock_db_session, modification_data)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_modifications_by_date_range(self, mock_db_session):
        """測試根據日期範圍取得修改記錄"""
        start_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        end_date = datetime.datetime(2025, 1, 31, 23, 59, 59)
        
        mock_records = [MagicMock(id=1), MagicMock(id=2)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await user.get_user_modifications_by_date_range(
            mock_db_session, start_date, end_date
        )
        
        assert len(result) == 2
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_modifications_by_user(self, mock_db_session):
        """測試根據使用者取得修改記錄"""
        mock_records = [
            MagicMock(id=1, user_name="test_user"),
            MagicMock(id=2, user_name="test_user")
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await user.get_user_modifications_by_user(
            mock_db_session, "test_user"
        )
        
        assert len(result) == 2
        assert all(r.user_name == "test_user" for r in result)
        mock_db_session.execute.assert_called_once()


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])