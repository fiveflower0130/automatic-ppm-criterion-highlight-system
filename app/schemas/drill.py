from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SearchDrill(BaseModel):
    lot_number: str
    drill_machine_id: Optional[int] = None
    drill_spindle_id: Optional[int] = None
    aoi_time: Optional[datetime] = None

class SearchFailrate(BaseModel):
    start_time: datetime
    end_time: datetime
    drill_machine_name: Optional[str] = None

class DrillReport(BaseModel):
    lot_number: str = Field(..., title="drill lot number") 
    machine_id: str = Field(..., title="drill machine id")
    spindle_id: str = Field(..., title="drill spindle id")
    aoi_time: datetime = Field(..., title="aoi time")
    image_path: Optional[str] =None
    image_update_time: Optional[datetime] = None
    contact_person: Optional[str] = None
    contact_time: Optional[datetime] = None
    comment: Optional[str] = None

class ReportUpdate(BaseModel):
    image_path: Optional[str] =None
    image_update_time: Optional[datetime] = None
    report_ee: Optional[str] = None
    report_time: Optional[datetime] = None
    comment: Optional[str] = None

class DrillInfo(BaseModel):
    product_name: str
    lot_number: str
    drill_machine_id: int
    drill_machine_name: str
    drill_spindle_id: int
    ppm_control_limit: int
    ppm: int
    judge_ppm: bool
    drill_time: Optional[datetime] = None
    cpk: Optional[float] = -1
    cp :Optional[float] = -1
    ca :Optional[float] = -1
    aoi_time: Optional[datetime] = None
    ratio_target : Optional[float] = -1
    image_path: Optional[str] = None
    image_update_time: Optional[datetime] = None
    report_ee: Optional[str] = None
    report_time: Optional[datetime] = None
    comment: Optional[str] = None

    class Config:
        orm_mode = True

