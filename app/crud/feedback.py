from app.models import mysql_models as models 
from app.schemas import feedback as schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# CRUD 操作：FeedbackRecord 相關資料表
async def update_drill_feedback_info(db: AsyncSession, search_items: dict, update_feedback: str):
    stmt = select(models.DrillInfo).filter(
        models.DrillInfo.lot_number == search_items["lot_number"],
        models.DrillInfo.drill_machine_name == search_items["drill_machine_name"],
        models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
        models.DrillInfo.drill_time == search_items["drill_time"]
    )
    result = await db.execute(stmt)
    data = result.scalars().first()
    if data:
        setattr(data, "feedback_result", update_feedback)
        await db.commit()
        await db.refresh(data)
        return True
    return False

async def create_feedback_record(db: AsyncSession, record_info: schemas.FeedbackRecord):
    db_feedback_record_info = models.FeedbackRecord(**record_info)
    db.add(db_feedback_record_info)
    await db.commit()
    await db.refresh(db_feedback_record_info)
    return db_feedback_record_info

async def get_feedback_record(db: AsyncSession, search_items: dict):
    stmt = select(
        models.FeedbackRecord.employee_id,
        models.FeedbackRecord.result,
        models.FeedbackRecord.comment,
        models.FeedbackRecord.update_time
    ).filter(
        models.FeedbackRecord.lot_number == search_items["lot_number"],
        models.FeedbackRecord.drill_machine_name == search_items["drill_machine_name"],
        models.FeedbackRecord.drill_spindle_id == search_items["drill_spindle_id"],
        models.FeedbackRecord.drill_time == search_items["drill_time"]
    )
    data = await db.execute(stmt)
    return data.scalars().all()

async def update_feedback_record(db: AsyncSession, update_items: dict):
    stmt = select(models.FeedbackRecord).filter(
        models.FeedbackRecord.lot_number == update_items["lot_number"],
        models.FeedbackRecord.drill_machine_name == update_items["drill_machine_name"],
        models.FeedbackRecord.drill_spindle_id == update_items["drill_spindle_id"],
        models.FeedbackRecord.drill_time == update_items["drill_time"],
        models.FeedbackRecord.employee_id == update_items["employee_id"]
    )
    result = await db.execute(stmt)
    data = result.scalars().first()
    if data:
        for key, value in update_items.items():
            setattr(data, key, value)
        await db.commit()
        await db.refresh(data)
        result = True
    return False

async def del_feedback_record(db: AsyncSession, search_items: dict):
    stmt = select(models.FeedbackRecord).filter(
        models.FeedbackRecord.lot_number == search_items["lot_number"],
        models.FeedbackRecord.drill_machine_name == search_items["drill_machine_name"],
        models.FeedbackRecord.drill_spindle_id == search_items["drill_spindle_id"],
        models.FeedbackRecord.drill_time == search_items["drill_time"],
        models.FeedbackRecord.employee_id == search_items["employee_id"]
    )
    result = await db.execute(stmt)
    data = result.scalars().first()
    if data:
        await db.delete(data)
        await db.commit()
        return True
    return False