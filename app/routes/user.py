import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from typing import Optional
from app.utils.response_helper import resp
from app.utils.redis_helper import get_cache, set_cache, exists_cache
from app.database.mysql import get_mysql_db
from app.crud import user as crud
from app.schemas.api import Resp as Response
from app.schemas import user as schemas

router = APIRouter()

@router.get("/api/drill/modification", response_model=Response)
async def get_user_modification_record(
    start_time: Optional[datetime.datetime]=None,
    end_time: Optional[datetime.datetime]=None,
    db: Session = Depends(get_mysql_db)
):
    try:
        key = f"mysql.k9.drill.modification.{start_time}.{end_time}" if (start_time and end_time) else f"mysql.k9.drill.modification"
        key_time = 60*5 if (start_time and end_time) else None
        if await exists_cache(key):
            data = await get_cache(key)
        else:
            if start_time and end_time:
                data = await crud.get_user_modification_record_by_datetime(db, start_time, end_time)
            else:
                data = await crud.get_user_modification_record_all(db)
            await set_cache(key, jsonable_encoder(data), ex=key_time)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/modification", response_model=Response)
async def add_user_modification_record(body: schemas.UserModificationRecord, db: Session = Depends(get_mysql_db)):
    if not body.employee_id:
        return resp("Employee ID could not be empty!")
    if not body.sql_command:
        return resp("SQL command could not be empty!")
    try:
        record_info = {
            "employee_id": body.employee_id,
            "sql_command": body.sql_command,
            "update_time": body.update_time if body.update_time else datetime.datetime.now()
        }
        data = await crud.create_user_modification_record(db, record_info)
        key = "mysql.k9.drill.modification"
        record_list = await crud.get_user_modification_record_all(db)
        await set_cache(key, jsonable_encoder(record_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))