from app.models import mysql_models as models 
from app.schemas import mail as schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# CRUD 操作：MailInfo 和 EEInfo 相關資料表
async def create_mail_info(db: AsyncSession, mail_info: schemas.MailInfo):
    db_mail_info = models.MailInfo(**mail_info)
    db.add(db_mail_info)
    await db.commit()
    await db.refresh(db_mail_info)
    return db_mail_info

async def create_ee_info(db: AsyncSession, ee_info: schemas.EEInfo):
    db_ee_info = models.EEInfo(**ee_info)
    db.add(db_ee_info)
    await db.commit()
    await db.refresh(db_ee_info)
    return db_ee_info

async def get_mail_info(db: AsyncSession):
    data = await db.execute(select(models.MailInfo))
    return data.scalars().all()

async def get_ee_info(db: AsyncSession):
    data = await db.execute(select(models.EEInfo))
    return data.scalars().all()

async def del_mail_info(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.MailInfo).filter(models.MailInfo.email == email)
    )
    mail_obj = result.scalars().first()
    if mail_obj:
        await db.delete(mail_obj)
        await db.commit()
        return True
    return False

async def del_ee_info(db: AsyncSession, ee_id: str):
    result = await db.execute(
            select(models.EEInfo).filter(models.EEInfo.ee_id == ee_id)
    )
    ee_obj = result.scalars().first()
    if ee_obj:
        await db.delete(ee_obj)
        await db.commit()
        return True
    return False
