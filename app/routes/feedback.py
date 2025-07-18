import json
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.response_helper import resp
from app.database.mysql import get_mysql_db 
from app.crud import feedback as crud
from app.schemas.api import Resp as Response
from app.schemas import feedback as schemas

router = APIRouter()


@router.patch("/api/drill/judge", response_model=Response)
async def update_drill_judge_feedback(body: schemas.DrillFeedback, db: AsyncSession = Depends(get_mysql_db)):
    if not body.lot_number:
        return resp("lot number could not be empty!")
    if not body.drill_machine_name:
        return resp("machine name could not be empty!")
    if body.drill_spindle_id is None:
        return resp("spindle id could not be empty!")
    if not body.drill_time:
        return resp("drill time could not be empty!")
    if not body.feedback_result:
        return resp("feedback result could not be empty!")
    try:
        search_items = dict(
            lot_number=body.lot_number,
            drill_machine_name=body.drill_machine_name,
            drill_spindle_id=body.drill_spindle_id,
            drill_time=body.drill_time
        )
        update_feedback = body.feedback_result
        data = await crud.update_drill_feedback_info(db, search_items, update_feedback)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.get("/api/drill/feedback", response_model=Response)
async def get_feedback_record(
    lot_number: str,
    drill_machine_name: str,
    drill_spindle_id: int,
    drill_time: datetime.datetime,
    db: AsyncSession = Depends(get_mysql_db)
):
    if not lot_number:
        return resp("Lot number could not be empty!")
    if not drill_machine_name:
        return resp("Drill machine name could not be empty!")
    if drill_spindle_id is None:
        return resp("Drill spindle id could not be empty!")
    if not drill_time:
        return resp("Drill time could not be empty!")
    try:
        search_items = {
            "lot_number": lot_number,
            "drill_machine_name": drill_machine_name,
            "drill_spindle_id": drill_spindle_id,
            "drill_time": drill_time
        }
        data = await crud.get_feedback_record(db, search_items)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.post("/api/drill/feedback", response_model=Response)
async def add_feedback_record(body: schemas.FeedbackRecord, db: AsyncSession = Depends(get_mysql_db)):
    if not body.employee_id:
        return resp("Employee ID could not be empty!")
    if not body.lot_number:
        return resp("Lot number could not be empty!")
    if not body.product_name:
        return resp("Product name could not be empty!")
    if not body.drill_machine_name:
        return resp("Drill machine name could not be empty!")
    try:
        record_info = body.dict()
        data = await crud.create_feedback_record(db, record_info)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.patch("/api/drill/feedback", response_model=Response)
async def update_feedback_record(body: schemas.FeedbackRecord, db: AsyncSession = Depends(get_mysql_db)):
    if not body.employee_id:
        return resp("Employee ID could not be empty!")
    if not body.result:
        return resp("Result could not be empty!")
    if not body.comment:
        return resp("Comment could not be empty!")
    if not body.update_time:
        return resp("Update time could not be empty!")
    try:
        update_info = body.dict()
        data = await crud.update_feedback_record(db, update_items=update_info)
        return resp(None, data)
    except Exception as err:
        return resp(str(err))

@router.delete("/api/drill/feedback", response_model=Response)
async def del_feedback_record(
    lot_number: str,
    drill_machine_name: str,
    drill_spindle_id: int,
    drill_time: datetime.datetime,
    employee_id: str,
    db: AsyncSession = Depends(get_mysql_db)
):
    if not lot_number:
        return resp("Lot number could not be empty!")
    if not drill_machine_name:
        return resp("Drill machine name could not be empty!")
    if drill_spindle_id is None:
        return resp("Drill spindle id could not be empty!")
    if not drill_time:
        return resp("Drill time could not be empty!")
    try:
        search_items = {
            "lot_number": lot_number,
            "drill_machine_name": drill_machine_name,
            "drill_spindle_id": drill_spindle_id,
            "drill_time": drill_time,
            "employee_id": employee_id
        }
        result = await crud.del_feedback_record(db, search_items)
        data = "Delete Success" if result == 1 else "Delete Fail"
        return resp(None, data)
    except Exception as err:
        return resp(str(err))