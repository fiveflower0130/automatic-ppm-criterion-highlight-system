from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserModificationRecord(BaseModel):
    employee_id: str
    sql_command: str
    update_time: Optional[datetime] = None

    class Config:
        orm_mode = True