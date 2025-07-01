from app.models import mssql_models as models 
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

def get_board_info_count(db: Session):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime !="")
    result = db.execute(stmt)
    count = len(result.scalars().all())
    return count

def get_board_info(db: Session, boardInfo_id: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.ID_B == boardInfo_id)
    result = db.execute(stmt)
    data = result.scalars().first()
    return data

def get_boards_info(db: Session, skip: int, limit: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime != "")
    result = db.execute(stmt)
    data = result.scalars().all()
    return data[skip:limit]
    

def get_board_info_by_first_aoitime(db: Session):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime != ""
    ).order_by(models.BoardInfo.AOITime)
    result = db.execute(stmt)
    data = result.scalars().first()
    return data

def get_board_info_by_last_aoitime(db: Session):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime != "",
        # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
    ).order_by(desc(models.BoardInfo.AOITime))
    result = db.execute(stmt)
    data = result.scalars().first()
    return data

def get_boards_info_by_datetime(db: Session, start_time:str):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime > start_time,
        # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
    ).order_by(models.BoardInfo.AOITime).limit(500)
    result = db.execute(stmt)
    data = result.scalars().all()
    return data

def get_boards_info_by_limit(db: Session, skip: int, limit: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime != "")
    result = db.execute(stmt)
    data = result.scalars().all()
    return data[skip:limit]

def get_measure_info(db: Session, board_id: int):
    stmt = select(models.MeasureInfo).filter(
        models.MeasureInfo.BoardID == board_id,
        models.MeasureInfo.ToolID == -1,
    )
    result = db.execute(stmt)
    data = result.scalars().first()
    return data

def get_product_name(db: Session, product_id: int):
    stmt = select(models.ProductInfo).filter(models.ProductInfo.ID_PD == product_id)
    result = db.execute(stmt)
    data = result.scalars().first()
    return data.Name_PD if data else None

def get_machine_name(db: Session, machine_id: int):
    stmt = select(models.MachineInfo).filter(models.MachineInfo.ID_DM == machine_id)
    result = db.execute(stmt)
    data = result.scalars().first()
    return data