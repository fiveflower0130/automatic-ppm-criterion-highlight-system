import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from app.utils.response_helper import resp
from app.utils.redis_helper import get_cache, set_cache, exists_cache
from app.database.mysql import get_mysql_db
from app.crud import mail as crud
from app.schemas.api import Resp as Response
from app.schemas import mail as schemas

router = APIRouter()

@router.get("/api/drill/mail", response_model=Response)
async def get_mail_list(db: AsyncSession = Depends(get_mysql_db)):
    key = "mysql.k9.drill.maillist"
    try:
        if await exists_cache(key):
            value = await get_cache(key)
            data = value
        else:
            data = await crud.get_mail_info(db)
            await set_cache(key, jsonable_encoder(data))
        print("mail info:", data)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.get("/api/drill/eelist", response_model=Response)
async def get_ee_list(db: AsyncSession = Depends(get_mysql_db)):
    key = "mysql.k9.drill.eelist"
    try:
        if await exists_cache(key):
            value = await get_cache(key)
            data = value
        else:
            data = await crud.get_ee_info(db)
            await set_cache(key, jsonable_encoder(data))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/mail", response_model=Response)
async def add_email_info(body: schemas.MailInfo, db: AsyncSession = Depends(get_mysql_db)):
    if not body.email:
        return resp("email could not be empty!")
    if not body.send_type:
        return resp("send type could not be empty!")
    key = "mysql.k9.drill.maillist"
    try:
        mail_info = {}
        mail_info["email"] = body.email
        mail_info["send_type"] = body.send_type
        data = await crud.create_mail_info(db, mail_info)
        mail_list = await crud.get_mail_info(db)
        await set_cache(key, jsonable_encoder(mail_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/eelist", response_model=Response)
async def add_ee_info(body: schemas.EEInfo, db: AsyncSession = Depends(get_mysql_db)):
    if not body.ee_id:
        return resp("EE ID could not be empty!")
    if not body.name:
        return resp("EE name could not be empty!")
    key = "mysql.k9.drill.eelist"
    try:
        ee_info = {}
        ee_info["ee_id"] = body.ee_id
        ee_info["name"] = body.name
        data = await crud.create_ee_info(db, ee_info)
        ee_list = await crud.get_ee_info(db)
        await set_cache(key, jsonable_encoder(ee_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.delete("/api/drill/mail", response_model=Response)
async def del_mail_info(email: str, db: AsyncSession = Depends(get_mysql_db)):
    if not email:
        raise HTTPException(status_code=422, detail="lot could not be empty")
    result = await crud.del_mail_info(db, email)
    data = "Delete Success" if result == 1 else "Delete Fail"
    key = "mysql.k9.drill.maillist"
    mail_list = await crud.get_mail_info(db)
    await set_cache(key, jsonable_encoder(mail_list))
    return resp(None, data)

@router.delete("/api/drill/eelist", response_model=Response)
async def del_ee_info(ee_id: str, db: AsyncSession = Depends(get_mysql_db)):
    if not ee_id:
        raise HTTPException(status_code=422, detail="lot could not be empty")
    result = await crud.del_ee_info(db, ee_id)
    data = "Delete Success" if result == 1 else "Delete Fail"
    key = "mysql.k9.drill.eelist"
    ee_list = await crud.get_ee_info(db)
    await set_cache(key, jsonable_encoder(ee_list))
    return resp(None, data)

