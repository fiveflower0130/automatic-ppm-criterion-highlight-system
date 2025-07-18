from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SearchFeedback(BaseModel):
    lot_number: str
    drill_machine_name: str
    drill_spindle_id: int
    drill_time: datetime
    employee_id: Optional[str] = None

class DrillFeedback(BaseModel):
    lot_number:str
    drill_machine_name: str
    drill_spindle_id: int
    drill_time: datetime
    feedback_result: str

class FeedbackRecord(BaseModel):
    product_name: str
    lot_number: str
    drill_machine_name: str
    drill_spindle_id: int
    drill_time: datetime
    employee_id: str
    result: str
    comment: str
    update_time: datetime

    class Config:
        orm_mode = True