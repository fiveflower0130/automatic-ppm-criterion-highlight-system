from app.models import mssql_models as models 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

async def get_board_info_count(db: AsyncSession):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime !="")
    result = await db.execute(stmt)
    count = len(result.scalars().all())
    return count

async def get_board_info(db: AsyncSession, boardInfo_id: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.ID_B == boardInfo_id)
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def get_boards_info(db: AsyncSession, skip: int, limit: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime != "")
    result = await db.execute(stmt)
    data = result.scalars().all()
    return data[skip:limit]
    

async def get_board_info_by_first_aoitime(db: AsyncSession):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime != ""
    ).order_by(models.BoardInfo.AOITime)
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def get_board_info_by_last_aoitime(db: AsyncSession):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime != "",
        # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
    ).order_by(desc(models.BoardInfo.AOITime))
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def get_boards_info_by_datetime(db: AsyncSession, start_time:str):
    stmt = select(models.BoardInfo).filter(
        models.BoardInfo.Lot != "",
        models.BoardInfo.AOITime > start_time,
        # models.BoardInfo.DrillMachineID.not_in([0, 2, 8, 14])
    ).order_by(models.BoardInfo.AOITime).limit(500)
    result = await db.execute(stmt)
    data = result.scalars().all()
    return data

async def get_boards_info_by_limit(db: AsyncSession, skip: int, limit: int):
    stmt = select(models.BoardInfo).filter(models.BoardInfo.AOITime != "")
    result = await db.execute(stmt)
    data = result.scalars().all()
    return data[skip:limit]

async def get_measure_info(db: AsyncSession, board_id: int):
    stmt = select(models.MeasureInfo).filter(
        models.MeasureInfo.BoardID == board_id,
        models.MeasureInfo.ToolID == -1,
    )
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data

async def get_product_name(db: AsyncSession, product_id: int):
    stmt = select(models.ProductInfo).filter(models.ProductInfo.ID_PD == product_id)
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data.Name_PD if data else None

async def get_machine_name(db: AsyncSession, machine_id: int):
    stmt = select(models.MachineInfo).filter(models.MachineInfo.ID_DM == machine_id)
    result = await db.execute(stmt)
    data = result.scalars().first()
    return data