import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import drill
from app.schemas.drill import DrillInfo, SearchDrill, SearchDrillByImageInfo
from app.models.mysql_models import DrillInfo as DrillInfoModel

class TestDrillCRUD:
    """DrillInfo CRUD 操作測試類別"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫 session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_get_drill_info_count(self, mock_db_session):
        """測試取得 DrillInfo 總數"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_drill_info_count(mock_db_session)
        
        assert result == 100
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_drill_info_by_last_aoitime(self, mock_db_session):
        """測試取得最後 AOI 時間的 DrillInfo"""
        mock_record = MagicMock()
        mock_record.aoi_time = datetime.datetime(2025, 1, 1, 12, 0, 0)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_drill_info_by_last_aoitime(mock_db_session)
        
        assert result.aoi_time == datetime.datetime(2025, 1, 1, 12, 0, 0)
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_drill_info_by_image_info(self, mock_db_session):
        """測試根據圖檔資訊取得 DrillInfo"""
        search_items = SearchDrillByImageInfo(
            lot_number="L001",
            machine_name="ND01",
            spindle_id="1",
            image_create_time="2025-01-01 12:00:00"
        )
        
        mock_records = [MagicMock(id=1, lot_number="L001")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_drill_info_by_image_info(mock_db_session, search_items)
        
        assert len(result) == 1
        assert result[0].lot_number == "L001"
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_drill_info(self, mock_db_session):
        """測試取得 DrillInfo 列表"""
        search_items = SearchDrill(
            lot_number="L001",
            start_time=datetime.datetime(2025, 1, 1, 0, 0, 0),
            end_time=datetime.datetime(2025, 1, 31, 23, 59, 59)
        )
        
        mock_records = [
            MagicMock(id=1, lot_number="L001"),
            MagicMock(id=2, lot_number="L001")
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_drill_info(mock_db_session, search_items)
        
        assert len(result) == 2
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_judge_info(self, mock_db_session):
        """測試取得判定資訊"""
        start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
        end_time = datetime.datetime(2025, 1, 31, 23, 59, 59)
        
        mock_records = [
            MagicMock(drill_machine_name="ND01", judge_ppm=1),
            MagicMock(drill_machine_name="ND01", judge_ppm=0)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_judge_info(mock_db_session, start_time, end_time)
        
        assert len(result) == 2
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_drill_info_check(self, mock_db_session):
        """測試檢查 DrillInfo 是否存在"""
        drill_info = DrillInfo(
            lot_number="L001",
            drill_machine_name="ND01",
            drill_spindle_id=1,
            aoi_time=datetime.datetime(2025, 1, 1, 12, 0, 0)
        )
        
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db_session.execute.return_value = mock_result
        
        result = await drill.get_drill_info_check(mock_db_session, drill_info)
        
        assert result == 1
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_drill_info(self, mock_db_session):
        """測試建立 DrillInfo"""
        drill_info = DrillInfo(
            lot_number="L001",
            drill_machine_name="ND01",
            drill_spindle_id=1,
            aoi_time=datetime.datetime(2025, 1, 1, 12, 0, 0),
            ppm=1000,
            judge_ppm=0
        )
        
        await drill.create_drill_info(mock_db_session, drill_info)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_drill_report_info_success(self, mock_db_session):
        """測試成功更新 DrillInfo 報告資訊"""
        mock_record = MagicMock(spec=DrillInfoModel)
        mock_record.id = 1
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_record
        mock_db_session.execute.return_value = mock_result
        
        update_data = {
            "image_path": "/path/to/image.jpg",
            "image_update_time": datetime.datetime.now()
        }
        
        result = await drill.update_drill_report_info(
            mock_db_session, 1, update_data
        )
        
        assert result == True
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_drill_report_info_not_found(self, mock_db_session):
        """測試更新不存在的 DrillInfo"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        update_data = {"image_path": "/path/to/image.jpg"}
        
        result = await drill.update_drill_report_info(
            mock_db_session, 999, update_data
        )
        
        assert result == False
        mock_db_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_bulk_create_drill_info(self, mock_db_session):
        """測試批次建立 DrillInfo"""
        drill_infos = [
            DrillInfo(
                lot_number=f"L{i:03d}",
                drill_machine_name="ND01",
                drill_spindle_id=1,
                aoi_time=datetime.datetime.now(),
                ppm=1000,
                judge_ppm=0
            )
            for i in range(10)
        ]
        
        await drill.bulk_create_drill_info(mock_db_session, drill_infos)
        
        assert mock_db_session.add.call_count == 10
        mock_db_session.commit.assert_called_once()


# 執行測試的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v"])