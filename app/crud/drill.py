from app.models import mysql_models as models 
from app.schemas import drill as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Dict, Any

# CRUD 操作：DrillInfo 相關資料表
async def get_drill_info_count(db: AsyncSession):
    stmt = select(func.count(models.DrillInfo.id))
    result = await db.execute(stmt)
    data = result.scalar()
    return data

async def get_drill_info_by_last_aoitime(db: AsyncSession):
    stmt = select(models.DrillInfo).order_by(desc(models.DrillInfo.aoi_time))
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def get_drill_info(db: AsyncSession, search_items: schemas.SearchDrill):
    if search_items["drill_machine_id"] and search_items["drill_spindle_id"] and search_items["aoi_time"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            )
        )
        return data.scalars().all()
    elif search_items["drill_machine_id"] and search_items["drill_spindle_id"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            )
        )
        return data.scalars().all()
    elif search_items["drill_spindle_id"] and search_items["aoi_time"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            )
        )
        return data.scalars().all()
    elif search_items["drill_machine_id"] and search_items["aoi_time"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            )
        )
        return data.scalars().all()
    elif search_items["drill_machine_id"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"]
            )
        )
        return data.scalars().all()
    elif search_items["drill_spindle_id"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            )
        )
        return data.scalars().all()
    elif search_items["aoi_time"]:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            )
        )
    else:
        data = await db.execute(
            select(models.DrillInfo).filter(
                models.DrillInfo.lot_number == search_items["lot_number"],
            )
        )
    return data.scalars().all()

async def get_judge_info(db: AsyncSession, start_time:datetime, end_time:datetime):
    stmt = select(models.DrillInfo).filter(models.DrillInfo.aoi_time.between(start_time, end_time))
    result = await db.execute(stmt)
    data = result.scalars().all()
    return data

async def get_drill_info_check(db: AsyncSession, drill_info: schemas.DrillInfo):
    stmt = select(models.DrillInfo).filter(
        models.DrillInfo.lot_number == drill_info["lot_number"],
        models.DrillInfo.drill_spindle_id == drill_info["drill_spindle_id"],
        models.DrillInfo.aoi_time == drill_info["drill_time"]
    )
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def create_drill_info(db: AsyncSession, drill_info: schemas.DrillInfo):
    db_drill_info = models.DrillInfo(**drill_info)
    db.add(db_drill_info)
    await db.commit()
    await db.refresh(db_drill_info)
    return db_drill_info

async def create_drill_info_all(db: AsyncSession, info_list: List[schemas.DrillInfo]):
    db_drill_info = [models.DrillInfo(**data) for data in info_list]
    db.add_all(db_drill_info)
    await db.commit()
    return True

async def update_drill_report_info(db: AsyncSession, search_items: schemas.SearchDrill, update_items: schemas.ReportUpdate):
    stmt = select(models.DrillInfo).filter(
        models.DrillInfo.lot_number == search_items["lot_number"],
        models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
        models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
        models.DrillInfo.aoi_time == search_items["aoi_time"]
    )
    result = await db.execute(stmt)
    data = result.scalars().first()

    if data:
        for key, value in update_items.items():
            setattr(data, key, value)
        await db.commit()
        await db.flush()
        await db.refresh(data)
        return True
    return False

async def get_drill_failrate_info_by_datetimelimit_and_machine_name(db: AsyncSession, search_items: schemas.SearchFailrate)->Dict[str, Any]:   
    async def get_counts_and_fail_rate(machine_name_filter) -> Dict[str, Any]:
        total_stmt = select(func.count(models.DrillInfo.id)).filter(
            machine_name_filter,
            models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"])
        )
        fail_stmt = select(func.count(models.DrillInfo.id)).filter(
            machine_name_filter,
            models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"]),
            models.DrillInfo.judge_ppm == 0
        )
        total_result = await db.execute(total_stmt)
        fail_result = await db.execute(fail_stmt)
        total_count = total_result.scalar()
        fail_count = fail_result.scalar()
        fail_rate = round(fail_count / total_count, 2) if total_count else 0
        return {"total_count": total_count, "fail_count": fail_count, "fail_rate": fail_rate}

    data = dict()
    if search_items.get("drill_machine_name"):
        machine_name = search_items["drill_machine_name"]
        machine_name_filter = models.DrillInfo.drill_machine_name == machine_name
        data.update(await get_counts_and_fail_rate(machine_name_filter))
    else:
        hitachi_filter = models.DrillInfo.drill_machine_name < "ND41"
        posalux_filter = models.DrillInfo.drill_machine_name > "ND40"
        data["hitachi"] = await get_counts_and_fail_rate(hitachi_filter)
        data["posalux"] = await get_counts_and_fail_rate(posalux_filter)
    return data

async def get_drill_failrate_info_by_datetimelimit_and_machine_name2(db: AsyncSession, search_items: schemas.SearchFailrate)->Dict[str, Any]:
    query = select(
        models.DrillInfo.drill_machine_name,
        models.DrillInfo.judge_ppm,
        models.DrillInfo.aoi_time
    ).filter(
        models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"])
    )
    if search_items.get("drill_machine_name"):
        query = query.filter(models.DrillInfo.drill_machine_name == search_items["drill_machine_name"])
    result = await db.execute(query)
    data = result.all()
    
    return data