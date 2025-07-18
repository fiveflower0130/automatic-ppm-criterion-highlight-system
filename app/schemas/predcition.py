from datetime import datetime
from pydantic import BaseModel

class PredictionRecord(BaseModel):
    image_path: str
    product_name: str
    classification_code: str
    classification_model: str
    mahalanobis_distance: float
    classification_time: datetime

    class Config:
        orm_mode = True