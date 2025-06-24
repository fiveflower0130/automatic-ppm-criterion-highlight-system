from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class PPMCriteriaLimitInfo(BaseModel):
    product_name: str
    ar: Optional[float] = -1
    ar_level: str
    ppm_limit: int
    modification: Optional[bool] = False
    update_time: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class PPMARLimitInfo(BaseModel):
    ar_level: Optional[str] = None
    lower_limit: Optional[float] = -1.0
    upper_limit: Optional[float] = -1.0
    ppm_limit: Optional[int] = 0.0
    update_time: Optional[datetime] = None

    class Config:
        orm_mode = True