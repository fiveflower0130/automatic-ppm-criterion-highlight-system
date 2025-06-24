from app.models import mysql_models as models 
from app.schemas import drill as schemas
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Dict, Any

# CRUD 操作：DrillInfo 相關資料表
async def get_drill_info_count(db: Session):
    data = db.query(models.DrillInfo).count()
    return data

async def get_drill_info_by_last_aoitime(db: Session):
    data = db.query(models.DrillInfo).order_by(desc(models.DrillInfo.aoi_time)).first()
    # data = db.query(func.max(models.DrillInfo.aoi_time)).scalar()
    return data

async def get_drill_info(db: Session, search_items: schemas.SearchDrill):
    if search_items["drill_machine_id"] and search_items["drill_spindle_id"] and search_items["aoi_time"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"], 
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            ).all()
    elif search_items["drill_machine_id"] and search_items["drill_spindle_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            ).all()
    elif search_items["drill_spindle_id"] and search_items["aoi_time"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            ).all()
    elif search_items["drill_machine_id"] and search_items["aoi_time"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"],
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            ).all()
    elif search_items["drill_machine_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_machine_id == search_items["drill_machine_id"]
            ).all()
    elif search_items["drill_spindle_id"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"]
            ).all()
    elif search_items["aoi_time"]:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
                models.DrillInfo.aoi_time == search_items["aoi_time"]
            ).all()
    else:
        data = db.query(models.DrillInfo).\
            filter(
                models.DrillInfo.lot_number == search_items["lot_number"], 
            ).all() 
    return data

async def get_judge_info(db: Session, start_time:datetime, end_time:datetime):
    data = db.query(models.DrillInfo).filter(models.DrillInfo.aoi_time.between(start_time, end_time)).all()
    return data

async def get_drill_info_check(db: Session, drill_info: schemas.DrillInfo):
    data = db.query(models.DrillInfo).\
        filter(
            models.DrillInfo.lot_number == drill_info["lot_number"],  
            models.DrillInfo.drill_spindle_id == drill_info["drill_spindle_id"],
            models.DrillInfo.aoi_time == drill_info["drill_time"]
        )
    
    result =  db.query(data.exists()).scalar() # True if data else False
    return result

async def create_drill_info(db: Session, drill_info: schemas.DrillInfo):
    db_drill_info = models.DrillInfo(**drill_info)
    db.add(db_drill_info)
    db.commit()
    db.refresh(db_drill_info)
    return db_drill_info

async def create_drill_info_all(db: Session, info_list: List[schemas.DrillInfo]):
    result = False
    db_drill_info = [models.DrillInfo(**data) for data in info_list]
    db.add_all(db_drill_info)
    db.commit()
    # db.refresh(db_drill_info)
    result = True
    return result

async def update_drill_report_info(db: Session, search_items: schemas.SearchDrill, update_items: schemas.ReportUpdate):
    result = False
    data = db.query(models.DrillInfo).\
        filter(
            models.DrillInfo.lot_number == search_items["lot_number"], 
            models.DrillInfo.drill_machine_id == search_items["drill_machine_id"], 
            models.DrillInfo.drill_spindle_id == search_items["drill_spindle_id"],
            models.DrillInfo.aoi_time == search_items["aoi_time"]
        ).first()

    if data:
        update_dict = update_items
        for key, value in update_dict.items():
            setattr(data, key, value)
        db.commit()
        db.flush()
        db.refresh(data)
        result = True
    return result

async def get_drill_failrate_info_by_datetimelimit_and_machine_name(db: Session, search_items: schemas.SearchFailrate)->Dict[str, Any]:
    
    def get_counts_and_fail_rate(machine_name_filter) -> Dict[str, Any]:
        total_count = db.query(func.count(models.DrillInfo.id)).filter(
            machine_name_filter,
            models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"])
        ).scalar()
        
        fail_count = db.query(func.count(models.DrillInfo.id)).filter(
            machine_name_filter,
            models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"]),
            models.DrillInfo.judge_ppm == 0
        ).scalar()
        
        fail_rate = round(fail_count / total_count, 2) if total_count else 0
        
        return {"total_count": total_count, "fail_count": fail_count, "fail_rate": fail_rate}

    data = dict()

    if search_items.get("drill_machine_name"):
        machine_name = search_items["drill_machine_name"]
        machine_name_filter = models.DrillInfo.drill_machine_name == machine_name
        data.update(get_counts_and_fail_rate(machine_name_filter))
    else:
        hitachi_filter = models.DrillInfo.drill_machine_name < "ND41"
        posalux_filter = models.DrillInfo.drill_machine_name > "ND40"
        
        data["hitachi"] = get_counts_and_fail_rate(hitachi_filter)
        data["posalux"] = get_counts_and_fail_rate(posalux_filter)
    
    return data

async def get_drill_failrate_info_by_datetimelimit_and_machine_name2(db: AsyncSession, search_items: schemas.SearchFailrate)->Dict[str, Any]:
    query = select(
        models.DrillInfo.drill_machine_name, 
        models.DrillInfo.judge_ppm, 
        models.DrillInfo.aoi_time
    ).where(
        models.DrillInfo.aoi_time.between(search_items["start_time"], search_items["end_time"])
    )
    
    if search_items.get("drill_machine_name"):
        query = query.where(models.DrillInfo.drill_machine_name == search_items["drill_machine_name"])
    
    result = db.execute(query)
    data = result.all()
    
    return data