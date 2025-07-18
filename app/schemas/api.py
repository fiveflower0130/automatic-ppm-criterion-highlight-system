from typing import Optional, Any
from pydantic import BaseModel

class Resp(BaseModel):
    code: str
    error: str
    data: Any