import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import feedback
from app.schemas.feedback import FeedbackRecord, SearchFeedback
from app.models.mysql_models import FeedbackRecord as FeedbackRecordModel

class TestFeedbackCRUD:
    """Feedback CRUD 操作測試類別"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫 session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_get_feedback_records(self, mock_db_session):
        """測試取得回饋記錄列表"""
        search_items = SearchFeedback(
            lot_number="L001",
            start_time=datetime.datetime(2025, 1, 1, 0, 0, 0),
            end_time=datetime.datetime(2025, 1, 31, 23, 59, 59)
        )
        
        mock_records = [
            MagicMock(id=1, lot_number="L001", feedback_content="Test 1"),
            MagicMock(id=2, lot_number="L001", feedback_content="Test 2")
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await feedback.get_feedback_records(mock_db_session, search_items)
        
        assert len(result) == 2
        assert result[0].feedback_content == "Test 1"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_feedback_by_id(self, mock_db_session):
        """測試根據 ID 取得回饋記錄"""
        mock_record = MagicMock(id=1, lot_number="L001")
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        result = await feedback.get_feedback_by_id(mock_db_session, 1)
        
        assert result.id == 1
        assert result.lot_number == "L001"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_feedback_record(self, mock_db_session):
        """測試建立回饋記錄"""
        feedback_data = FeedbackRecord(
            lot_number="L001",
            drill_machine_name="ND01",
            feedback_content="測試回饋",
            feedback_user="test_user",
            feedback_time=datetime.datetime.now()
        )
        
        await feedback.create_feedback_record(mock_db_session, feedback_data)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_feedback_record(self, mock_db_session):
        """測試更新回饋記錄"""
        mock_record = MagicMock(spec=FeedbackRecordModel)
        mock_record.id = 1
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        update_data = {
            "feedback_content": "更新的回饋",
            "status": "已處理"
        }
        
        result = await feedback.update_feedback_record(
            mock_db_session, 1, update_data
        )
        
        assert result == True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_feedback_record(self, mock_db_session):
        """測試刪除回饋記錄"""
        mock_record = MagicMock(spec=FeedbackRecordModel)
        mock_record.id = 1
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        result = await feedback.delete_feedback_record(mock_db_session, 1)
        
        assert result == True
        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])