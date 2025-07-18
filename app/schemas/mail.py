from pydantic import BaseModel

class MailInfo(BaseModel):
    email: str
    send_type: str

class EEInfo(BaseModel):
    ee_id: str
    name: str