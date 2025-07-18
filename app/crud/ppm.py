from app.models import mysql_models as models 
from app.schemas import ppm as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List


# CRUD 操作：PPMArLimitInfo 和 PPMCriteriaLimitInfo 相關資料表
async def get_ppm_ar_limit_info_by_level(db: AsyncSession, ar_level:str):
    stmt = select(models.PPMArLimitInfo).filter(models.PPMArLimitInfo.ar_level == ar_level)
    data = await db.execute(stmt)
    return data.scalars().first()

async def get_ppm_ar_limit_info(db: AsyncSession):
    stmt = select(models.PPMArLimitInfo).order_by(models.PPMArLimitInfo.ar_level)
    data = await db.execute(stmt)
    return data.scalars().all()

async def create_ppm_ar_limit_info(db: AsyncSession, info: schemas.PPMARLimitInfo):
    db_ppm_ar_info = models.PPMArLimitInfo(**info)
    db.add(db_ppm_ar_info)
    await db.commit()
    await db.refresh(db_ppm_ar_info)
    return db_ppm_ar_info

async def update_ppm_ar_limit_info(db: AsyncSession, update_info: List[schemas.PPMARLimitInfo]):
    await db.execute(delete(models.PPMArLimitInfo))
    db_ppm_ar_info = [models.PPMArLimitInfo(**data) for data in update_info]
    db.add_all(db_ppm_ar_info)
    await db.commit()
    return True
    # data = db.query(models.PPMArLimitInfo).\
    #     filter(
    #         models.PPMArLimitInfo.ar_level == update_items["ar_level"], 
    #     ).first()

    # if data:
    #     update_dict = update_items
    #     for key, value in update_dict.items():
    #         setattr(data, key, value)
    #     db.commit()
    #     db.flush()
    #     db.refresh(data)
    #     result = True
    # else:
    #     db_ppm_ar_info = models.PPMArLimitInfo(**update_items)
    #     db.add(db_ppm_ar_info)
    #     db.commit()
    #     db.refresh(db_ppm_ar_info)
    #     result = True
    # return result

async def del_ppm_ar_limit_info(db: AsyncSession, ar_level: str):
    stmt = select(models.PPMArLimitInfo).filter(models.PPMArLimitInfo.ar_level == ar_level)
    result = await db.execute(stmt)
    obj = result.scalars().first()
    if obj:
        await db.delete(obj)
        await db.commit()
        return True
    return False

async def get_ppm_criteria_limit_info(db: AsyncSession, product_name: str):
    stmt = select(models.PPMCriteriaLimitInfo).filter(models.PPMCriteriaLimitInfo.product_name == product_name)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_ppm_criteria_limit_info_all(db: AsyncSession):
    stmt = select(models.PPMCriteriaLimitInfo).order_by(models.PPMCriteriaLimitInfo.id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_ppm_criteria_limit_info_by_datetime(db: AsyncSession, start_time:datetime, end_time:datetime):
    stmt = select(models.PPMCriteriaLimitInfo).filter(models.PPMCriteriaLimitInfo.update_time.between(start_time, end_time))
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_ppm_criteria_limit_info(db: AsyncSession, info: schemas.PPMCriteriaLimitInfo):
    db_ppm_criteria_info = models.PPMCriteriaLimitInfo(**info)
    db.add(db_ppm_criteria_info)
    await db.commit()
    await db.refresh(db_ppm_criteria_info)
    return db_ppm_criteria_info

async def create_ppm_criteria_limit_info_all(db: AsyncSession, info_list: List[schemas.PPMCriteriaLimitInfo]):
    result = False
    db_ppm_criteria_info = [models.PPMCriteriaLimitInfo(**data) for data in info_list]
    db.add_all(db_ppm_criteria_info)
    await db.commit()
    return True

async def update_ppm_criteria_limit_info(db: AsyncSession, update_items: schemas.PPMCriteriaLimitInfo):
    stmt = select(models.PPMCriteriaLimitInfo).filter(
        models.PPMCriteriaLimitInfo.product_name == update_items.product_name
    )
    result = await db.execute(stmt)
    obj = result.scalars().first()
    if obj:
        for key, value in update_items.items():
            setattr(obj, key, value)
        await db.commit()
        await db.refresh(obj)
        return True
    return False

async def del_ppm_criteria_limit_info(db: AsyncSession, product_name: str):
    stmt = select(models.PPMCriteriaLimitInfo).filter(models.PPMCriteriaLimitInfo.product_name == product_name)
    result = await db.execute(stmt)
    obj = result.scalars().first()
    if obj:
        await db.delete(obj)
        await db.commit()
        return True
    return False