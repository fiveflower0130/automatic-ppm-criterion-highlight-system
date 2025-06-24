from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

class MailInfo(BaseModel):
    email: str
    send_type: str

class EEInfo(BaseModel):
    ee_id: str
    name: str