from app.models import mysql_models as models 
from app.schemas import user as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# CRUD 操作：UserModificationRecord 相關資料表
async def get_user_modification_record_by_datetime(db: AsyncSession, start_time: datetime, end_time: datetime):
    stmt = (
        select(models.UserModificationRecord)
        .filter(models.UserModificationRecord.update_time.between(start_time, end_time))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_user_modification_record_all(db: AsyncSession):
    stmt = select(models.UserModificationRecord)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_user_modification_record(db: AsyncSession, record_info: schemas.UserModificationRecord):
    db_user_modification_record_info = models.UserModificationRecord(**record_info)
    db.add(db_user_modification_record_info)
    await db.commit()
    await db.refresh(db_user_modification_record_info)
    return db_user_modification_record_info