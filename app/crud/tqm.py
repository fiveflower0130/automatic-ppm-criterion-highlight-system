from app.models import mssql_models as models 
from sqlalchemy.orm import Session
from sqlalchemy import desc


async def get_board_info_count(db: Session):
    data = db.query(models.BoardInfo).filter(models.BoardInfo.AOITime !="").count()
    return data

async def get_board_info(db: Session, boardInfo_id: int):
    data = db.query(models.BoardInfo).filter(models.BoardInfo.ID_B == boardInfo_id).first()
    return data

async def get_boards_info(db: Session, skip: int, limit: int):
    data = db.query(models.BoardInfo).filter(models.BoardInfo.AOITime !="").limit(limit).all()
    print("temp_limit: ",skip, " limit: ",limit)
    data = data[skip:limit]
    return data

async def get_board_info_by_first_aoitime(db: Session):
    data = db.query(models.BoardInfo).\
        filter(
            models.BoardInfo.Lot !="",
            models.BoardInfo.AOITime !="",
            # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
        ).order_by(models.BoardInfo.AOITime).first()
    return data

async def get_board_info_by_last_aoitime(db: Session):
    data = db.query(models.BoardInfo).\
        filter(
            models.BoardInfo.Lot !='',
            models.BoardInfo.AOITime !='',
            # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
        ).order_by(desc(models.BoardInfo.AOITime)).first()
    return data

async def get_boards_info_by_datetime(db: Session, start_time):
    data = db.query(models.BoardInfo).\
        filter(
            # models.BoardInfo.AOITime.between(start_time, end_time),
            models.BoardInfo.Lot !="",
            models.BoardInfo.AOITime > start_time,
            # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
        ).order_by(models.BoardInfo.AOITime).limit(500).all()
    return data

async def get_boards_info_by_limit(db: Session, skip: int, limit: int):
    # data = db.query(models.BoardInfo).all()
    data = db.query(models.BoardInfo).filter(models.BoardInfo.AOITime !="").limit(limit).all()
    print("temp_limit: ",skip, " limit: ",limit)
    # print("board info: ",data[0].__dict__)
    data = data[skip:limit]
    return data

async def get_measure_info(db: Session, board_id: int):
    data = db.query(models.MeasureInfo).\
        filter(
            models.MeasureInfo.BoardID == board_id, 
            models.MeasureInfo.ToolID == -1, 
        ).first()
    return data

async def get_product_name(db: Session, product_id: int):
    data = db.query(models.ProductInfo).filter(models.ProductInfo.ID_PD == product_id).first()
    return data.Name_PD

async def get_machine_name(db: Session, machine_id: int):
    data = db.query(models.MachineInfo).filter(models.MachineInfo.ID_DM == machine_id).first()
    return data