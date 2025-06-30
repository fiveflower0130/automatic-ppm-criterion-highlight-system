from app.models import mysql_models as models 
from app.schemas import predcition as schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

async def create_prediction_record_all(db: AsyncSession, info_list: List[schemas.PredictionRecord]):
    db_prediction_info = [models.AIPredictionRecord(**data) for data in info_list]
    db.add_all(db_prediction_info)
    await db.commit()
    return True

async def get_prediction_record_check(db: AsyncSession, image_path: str):
    stmt = select(models.AIPredictionRecord).filter(models.AIPredictionRecord.image_path == image_path)
    result = await db.execute(stmt)
    exists = result.scalars().first() is not None
    return exists