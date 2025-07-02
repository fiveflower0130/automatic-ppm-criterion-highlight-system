import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from typing import Optional
from app.utils.response_helper import resp
from app.utils.redis_helper import get_cache, set_cache, exists_cache
from app.utils.data_transfer import DataTransfer
from app.database.mysql import get_mysql_db
from app.crud import ppm as crud
from app.schemas.api import Resp as Response
from app.schemas import ppm as schemas

transfer = DataTransfer()
router = APIRouter()

@router.get("/api/drill/criteria", response_model=Response)
async def get_ppm_criteria_limit_info(
    start_time: Optional[datetime.datetime]=None,
    end_time: Optional[datetime.datetime]=None,
    db: AsyncSession = Depends(get_mysql_db)
):
    try:
        if start_time and end_time:
            key = f"mysql.k9.drill.criteria.{start_time}.{end_time}"
        else:
            key = f"mysql.k9.drill.criteria"
        if await exists_cache(key):
            data = await get_cache(key)
        else:
            if start_time and end_time:
                data = await crud.get_ppm_criteria_limit_info_by_datetime(db, start_time, end_time)
            else:
                data = await crud.get_ppm_criteria_limit_info_all(db)
            await set_cache(key, jsonable_encoder(data))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/criteria", response_model=Response)
async def add_ppm_criteria_limit_info(body: schemas.PPMCriteriaLimitInfo, db: AsyncSession = Depends(get_mysql_db)):
    if not body.product_name:
        return resp("Product Name could not be empty!")
    if not body.ar:
        return resp("AR could not be empty!")
    if not body.ar_level:
        return resp("AR Level could not be empty!")
    if not body.ppm_limit:
        return resp("PPM Limit could not be empty!")
    if not isinstance(body.modification, bool):
        return resp("Modification could not be empty!")
    if not body.update_time:
        return resp("Update Time could not be empty!")
    try:
        ppm_criteria_limit_info = {
            "product_name": body.product_name,
            "ar": body.ar if body.ar else 0,
            "ar_level": body.ar_level if body.ar_level else None,
            "ppm_limit": body.ppm_limit if body.ppm_limit else 0,
            "modification": body.modification,
            "update_time": body.update_time if body.update_time else None
        }
        data = await crud.create_ppm_criteria_limit_info(db, ppm_criteria_limit_info)
        key = "mysql.k9.drill.criteria"
        criteria_limit_list = await crud.get_ppm_criteria_limit_info_all(db)
        await set_cache(key, jsonable_encoder(criteria_limit_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.patch("/api/drill/criteria", response_model=Response)
async def update_ppm_criteria_limit_info(body: schemas.PPMCriteriaLimitInfo, db: AsyncSession = Depends(get_mysql_db)):
    if not body.product_name:
        return resp("Product Name could not be empty!")
    if not body.update_time:
        return resp("Update Time could not be empty!")
    update_items = {
        "product_name": body.product_name if body.product_name else None,
        "ar": body.ar if body.ar else 0,
        "ar_level": body.ar_level if body.ar_level else None,
        "ppm_limit": body.ppm_limit if body.ppm_limit else 0,
        "modification": body.modification if body.modification else False,
        "update_time": body.update_time if body.update_time else None
    }
    try:
        data = await crud.update_ppm_criteria_limit_info(db, update_items)
        key = "mysql.k9.drill.criteria"
        criteria_limit_list = await crud.get_ppm_criteria_limit_info_all(db)
        await set_cache(key, jsonable_encoder(criteria_limit_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.delete("/api/drill/criteria", response_model=Response)
async def del_ppm_criteria_limit_info(product_name: str, db: AsyncSession = Depends(get_mysql_db)):
    if not product_name:
        raise HTTPException(status_code=422, detail="Product Name could not be empty")
    result = await crud.del_ppm_criteria_limit_info(db, product_name)
    data = "Delete Success" if result == 1 else "Delete Fail"
    key = "mysql.k9.drill.arlimit"
    criteria_limit_list = await crud.get_ppm_criteria_limit_info_all(db)
    await set_cache(key, jsonable_encoder(criteria_limit_list))
    return resp(None, data)

@router.get("/api/drill/arlimit", response_model=Response)
async def get_ppm_ar_limit_info(ar_level: str, db: AsyncSession = Depends(get_mysql_db)):
    try:
        if not ar_level:
            key = f"mysql.k9.drill.arlimit"
        else:
            key = f"mysql.k9.drill.arlimit.{ar_level}"
        if await exists_cache(key):
            data = await get_cache(key)
        else:
            if not ar_level:
                data = await crud.get_ppm_ar_limit_info(db)
            else:
                data = await crud.get_ppm_ar_limit_info_by_level(db, ar_level)
            await set_cache(key, jsonable_encoder(data))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/arlimit", response_model=Response)
async def update_ppm_ar_limit_info(body: dict, db: AsyncSession = Depends(get_mysql_db)):
    if not body.get("update_data"):
        return resp("AR Level limit data could not be empty!")
    try:
        data = await crud.update_ppm_ar_limit_info(db, body["update_data"])
        ar_limit_key = "mysql.k9.drill.arlimit"
        ar_limit_list = await crud.get_ppm_ar_limit_info(db)
        await set_cache(ar_limit_key, jsonable_encoder(ar_limit_list))
        criteria_data = await crud.get_ppm_criteria_limit_info_all(db)
        if not criteria_data:
            raise HTTPException(status_code=404, detail="PPM criteria limit data not found!")
        for c_data in criteria_data:
            if c_data.modification == False:
                update_items = await transfer.get_ppm_criteria_limit_info(
                    product_name=c_data.product_name,
                    ar_value=c_data.ar,
                    ar_info=ar_limit_list
                )
                await crud.update_ppm_criteria_limit_info(db, update_items)
        criteria_key = "mysql.k9.drill.criteria"
        criteria_limit_list = await crud.get_ppm_criteria_limit_info_all(db)
        await set_cache(criteria_key, jsonable_encoder(criteria_limit_list))
        return resp(None, data)
    except Exception as err:
        return resp(str(err))