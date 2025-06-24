from app.models import mysql_models as models 
from app.schemas import mail as schemas
from sqlalchemy.orm import Session, Query

# CRUD 操作：MailInfo 和 EEInfo 相關資料表
async def create_mail_info(db: Session, mail_info: schemas.MailInfo):
    db_mail_info = models.MailInfo(**mail_info)
    db.add(db_mail_info)
    db.commit()
    db.refresh(db_mail_info)
    return db_mail_info

async def create_ee_info(db: Session, ee_info: schemas.EEInfo):
    db_ee_info = models.EEInfo(**ee_info)
    db.add(db_ee_info)
    db.commit()
    db.refresh(db_ee_info)
    return db_ee_info

async def get_mail_info(db: Session):
    data = db.query(models.MailInfo).all()
    return data

async def get_ee_info(db: Session):
    data = db.query(models.EEInfo).all()
    return data

async def del_mail_info(db: Session, email: str):
    data = db.query(models.MailInfo).\
        filter(
            models.MailInfo.email == email
        ).delete()
    db.commit()
    return data

async def del_ee_info(db: Session, ee_id: schemas.EEInfo):
    data = db.query(models.EEInfo).\
        filter(
            models.EEInfo.ee_id == ee_id,  
        ).delete()
    db.commit()
    return data
