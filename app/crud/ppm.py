from app.models import mysql_models as models 
from app.schemas import ppm as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List


# CRUD 操作：PPMArLimitInfo 和 PPMCriteriaLimitInfo 相關資料表
async def get_ppm_ar_limit_info_by_level(db: Session, ar_level:str):
    data = db.query(models.PPMArLimitInfo).filter(models.PPMArLimitInfo.ar_level == ar_level).first()
    return data

async def get_ppm_ar_limit_info(db: Session):
    data = db.query(models.PPMArLimitInfo).order_by(models.PPMArLimitInfo.ar_level).all()
    return data

async def create_ppm_ar_limit_info(db: Session, info: schemas.PPMARLimitInfo):
    db_ppm_ar_info = models.PPMArLimitInfo(**info)
    db.add(db_ppm_ar_info)
    db.commit()
    db.refresh(db_ppm_ar_info)
    return db_ppm_ar_info

async def update_ppm_ar_limit_info(db: Session, update_info: List[schemas.PPMARLimitInfo]):
    result = False
    db.query(models.PPMArLimitInfo).delete()
    # paste new data
    db_ppm_ar_info = [models.PPMArLimitInfo(**data) for data in update_info]
    db.add_all(db_ppm_ar_info)
    db.commit()
    result = True
    return result
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

async def del_ppm_ar_limit_info(db: Session, ar_level: str):
    data = db.query(models.PPMArLimitInfo).\
        filter(
            models.PPMArLimitInfo.ar_level == ar_level,  
        ).delete()
    db.commit()
    return data

async def get_ppm_criteria_limit_info(db: Session, product_name: str):
    data = db.query(models.PPMCriteriaLimitInfo).filter(models.PPMCriteriaLimitInfo.product_name == product_name).first()
    return data

async def get_ppm_criteria_limit_info_all(db: Session):
    data = db.query(models.PPMCriteriaLimitInfo).order_by(models.PPMCriteriaLimitInfo.id).all()
    return data

async def get_ppm_criteria_limit_info_by_datetime(db: Session, start_time:datetime, end_time:datetime):
    data = db.query(models.PPMCriteriaLimitInfo).filter(models.PPMCriteriaLimitInfo.update_time.between(start_time, end_time)).all()
    return data

async def create_ppm_criteria_limit_info(db: Session, info: schemas.PPMCriteriaLimitInfo):
    db_ppm_criteria_info = models.PPMCriteriaLimitInfo(**info)
    db.add(db_ppm_criteria_info)
    db.commit()
    db.refresh(db_ppm_criteria_info)
    return db_ppm_criteria_info

async def create_ppm_criteria_limit_info_all(db: Session, info_list: List[schemas.PPMCriteriaLimitInfo]):
    result = False
    db_ppm_criteria_info = [models.PPMCriteriaLimitInfo(**data) for data in info_list]
    db.add_all(db_ppm_criteria_info)
    db.commit()
    # db.refresh(db_drill_info)
    result = True
    return result

async def update_ppm_criteria_limit_info(db: Session, update_items: schemas.PPMCriteriaLimitInfo):
    result = False
    data = db.query(models.PPMCriteriaLimitInfo).\
        filter(
            models.PPMCriteriaLimitInfo.product_name == update_items["product_name"], 
        ).first()

    if data:
        update_dict = update_items
        for key, value in update_dict.items():
            setattr(data, key, value)
        db.commit()
        db.flush()
        db.refresh(data)
        result = True
    return result

async def del_ppm_criteria_limit_info(db: Session, product_name: str):
    data = db.query(models.PPMCriteriaLimitInfo).\
        filter(
            models.PPMCriteriaLimitInfo.product_name == product_name,  
        ).delete()
    db.commit()
    return data