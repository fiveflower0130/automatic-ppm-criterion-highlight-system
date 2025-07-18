from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, Float
from app.database.mssql import mssql_base

class BoardInfo(mssql_base):
    __tablename__ = "tBoard"
    ID_B = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer)
    DrillMachineID = Column(Integer)
    DrillSpindleID = Column(Integer)
    DrillTime = Column(String)
    AOITime = Column(String)
    Lot = Column(String, index=True)

class MeasureInfo(mssql_base):
    __tablename__ = "tMeasure"
    ID_M = Column(Integer, primary_key=True, index=True)
    BoardID = Column(Integer, index=True)
    ToolID = Column(Integer)
    CA_Z_Before = Column(Float)
    CP_Z_Before = Column(Float)
    Cpk_Z_Before = Column(Float)
    RatioInTarget_Before = Column(Float)

class ProductInfo(mssql_base):
    __tablename__ = "tProduct"
    ID_PD = Column(Integer, primary_key=True, index=True)
    Name_PD = Column(String)

class MachineInfo(mssql_base):
    __tablename__ = "tDrillMachine"
    ID_DM = Column(Integer, primary_key=True, index=True)
    Name_DM = Column(String)

# 若要自動建立資料表，請取消下列註解
# MSSQLBase.metadata.create_all(bind=mssql_engine)
