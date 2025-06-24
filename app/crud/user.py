from app.models import mysql_models as models 
from app.schemas import ppm as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List

# CRUD 操作：UserModificationRecord 相關資料表
async def get_user_modification_record_by_datetime(db: Session, start_time:datetime, end_time:datetime):
    data = db.query(models.UserModificationRecord).filter(models.UserModificationRecord.update_time.between(start_time, end_time)).all()
    return data

async def get_user_modification_record_all(db: Session):
    data = db.query(models.UserModificationRecord).all()
    return data

async def create_user_modification_record(db: Session, record_info: schemas.UserModificationRecord):
    db_user_modification_record_info = models.UserModificationRecord(**record_info)
    db.add(db_user_modification_record_info)
    db.commit()
    db.refresh(db_user_modification_record_info)
    return db_user_modification_record_info