import datetime

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from app.routes import drill_router, feedback_router, mail_router, ppm_router, user_router
from app.services.tqm_service import TQMProcessorConfig, TQMProcessor
from app.utils.logger import Logger

logger = Logger().get_logger()
app = FastAPI()

# 註冊路由
app.include_router(drill_router)
app.include_router(feedback_router)
app.include_router(user_router)
app.include_router(mail_router)
app.include_router(ppm_router)

# 初始化 TQM 處理器
tqm_processor = TQMProcessor(
    config=TQMProcessorConfig(
        max_db_workers=5,
        batch_size=500,
        enable_email=False,
        enable_save=False
    )
)

@app.get("/", summary="Root Endpoint", description="Welcome message for the AUTO PPM API")
async def root():
    return {"message": "Welcome to the AUTO PPM API!"}

# 設定定時任務
@app.on_event("startup")
@repeat_every(seconds=60*10, logger=logger, raise_exceptions=True)
async def loop_task_run_tqm_process():
    await tqm_processor.run_process()
    print(f"-----------------Mission Completed for 'loop_task_run_tqm_process' at {datetime.datetime.now()}------------------")
