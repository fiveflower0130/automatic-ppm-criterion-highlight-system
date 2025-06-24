from app.models import mysql_models as models 
from app.schemas import predcition as schemas
from sqlalchemy.orm import Session
from typing import List

async def create_prediction_record_all(db: Session, info_list: List[schemas.PredictionRecord]):
    result = False
    db_prediction_info = [models.AIPredictionRecord(**data) for data in info_list]
    db.add_all(db_prediction_info)
    db.commit()
    # db.refresh(db_drill_info)
    result = True
    return result

async def get_prediction_record_check(db: Session, image_path: str):
    
    data = db.query(models.AIPredictionRecord).filter(models.AIPredictionRecord.image_path == image_path)
    result =  db.query(data.exists()).scalar() # True if data else False
    
    return result