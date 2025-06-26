import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from typing import Optional
from app.utils.response_helper import resp
from app.utils.redis_helper import get_cache, set_cache, exists_cache
from app.utils.data_transfer import DataTransfer
from app.database.mysql import get_mysql_db
from app.crud import drill as crud
from app.schemas.api import Resp as Response
from app.schemas import drill as schemas

transfer = DataTransfer()
router = APIRouter()

@router.get("/api/drill/judge", response_model=Response)
async def get_drill_judge_result(
    start_time: datetime.datetime, end_time: datetime.datetime, db: Session = Depends(get_mysql_db)
):
    if start_time and not end_time:
        raise HTTPException(status_code=422, detail="end_time could not be empty")
    if end_time and not start_time:
        raise HTTPException(status_code=422, detail="start_time could not be empty")
    try:
        data = await crud.get_judge_info(db, start_time, end_time)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.put("/api/drill/report", response_model=Response)
async def update_drill_report_info(body: schemas.DrillReport, db: Session = Depends(get_mysql_db)):
    if not body.lot_number:
        return resp("lot number could not be empty!")
    if not body.machine_id:
        return resp("machine id could not be empty!")
    if not body.spindle_id:
        return resp("spindle id could not be empty!")
    if not body.aoi_time:
        return resp("spindle id could not be empty!")
    search_items = {}
    update_items = {}
    try:
        search_items["lot_number"] = body.lot_number
        search_items["drill_machine_id"] = int(body.machine_id)
        search_items["drill_spindle_id"] = int(body.spindle_id)
        search_items["aoi_time"] = body.aoi_time
        update_items["image_path"] = body.image_path if body.image_path else None
        update_items["image_update_time"] = body.image_update_time if body.image_update_time else None
        update_items["report_ee"] = body.contact_person if body.contact_person else None
        update_items["report_time"] = body.contact_time if body.contact_time else None
        update_items["comment"] = body.comment if body.comment else None
        data = await crud.update_drill_report_info(db, search_items, update_items)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.get("/api/drill/failrate", response_model=Response)
async def get_drill_failrate_info(
    start_time: str,
    end_time: str,
    freq_type: str,
    drill_machine_name: str = None,
    db: Session = Depends(get_mysql_db)
):
    if not start_time:
        return resp("Start time could not be empty!")
    if not transfer.validate_datetime_format(start_time):
        return resp("Start time format error!")
    if not end_time:
        return resp("End time could not be empty!")
    if not transfer.validate_datetime_format(end_time):
        return resp("End time format error!")
    if not freq_type or freq_type not in ["day", "week", "month"]:
        return resp("Freq type could not be empty!")
    try:
        key = f"mysql.k9.drill.failrate.{start_time}.{end_time}.{freq_type}.{drill_machine_name}"
        if await exists_cache(key):
            data = await get_cache(key)
        else:
            search_items = {
                "start_time": start_time,
                "end_time": end_time,
                "drill_machine_name": drill_machine_name
            }
            search_data = await crud.get_drill_failrate_info_by_datetimelimit_and_machine_name2(db, search_items)
            datetime_limit = transfer.get_datetime_transfer(start_time, end_time, freq_type)
            data = transfer.get_failrate_filter_data(search_data, datetime_limit, drill_machine_name)
            await set_cache(key, jsonable_encoder(data), ex=60*10)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))