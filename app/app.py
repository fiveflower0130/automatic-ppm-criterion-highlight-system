import asyncio
import datetime

from app.services.email_service import EmailClient
from fastapi import FastAPI
# from fastapi_utils.tasks import repeat_every
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routes import drill_router, feedback_router, mail_router, ppm_router, user_router
from app.services.tqm_service import TQMProcessorConfig, TQMProcessor
from app.services.backup_service import BackupProcessorConfig, BackupProcessor
from app.utils.logger import Logger
from app.config import Config

logger = Logger().get_logger()
app = FastAPI()

# 註冊路由路徑
app.include_router(drill_router)
app.include_router(feedback_router)
app.include_router(user_router)
app.include_router(mail_router)
app.include_router(ppm_router)

# 初始化排程器
scheduler = AsyncIOScheduler()

# 初始化Email服務
email_client = EmailClient()

# 初始化 TQM 處理器
tqm_processor = TQMProcessor(
    work_config=TQMProcessorConfig(
        max_db_workers=5,
        batch_size=500,
        enable_email=False,
        enable_save=False
    ),
    email_client=email_client,
    email_host=Config.EMAIL_HOST
)
# 初始化備份服務
backup_processor = BackupProcessor(
    connection_config=BackupProcessorConfig(
        remote_path=Config.BACKUP_SRC_PATH,
        username=Config.BACKUP_AD_ACCOUNT,
        password=Config.BACKUP_AD_PASSWORD,
        domain=Config.BACKUP_AD_DOMAIN,
        retry=3
    ),
    email_client=email_client,
    email_host=Config.EMAIL_HOST
)

@app.get("/", summary="Root Endpoint", description="Welcome message for the AUTO PPM API")
async def root():
    return {"message": "Welcome to the AUTO PPM API!"}

# # 設定TQM定時任務
# @app.on_event("startup")
# @repeat_every(seconds=60*10, logger=logger, raise_exceptions=True)
# async def loop_task_run_tqm_process():
#     await tqm_processor.run_process()
#     print(f"-----------------Mission Completed for 'loop_task_run_tqm_process' at {datetime.datetime.now()}------------------")


# ------設定定時排程任務的異步function------
async def run_tqm_process():
    await tqm_processor.run_process()
    #logger.info(f"-----------------Mission Completed for 'run_tqm_process' at {datetime.datetime.now()}------------------")

async def run_backup_process():
    await backup_processor.run_process()
    # logger.info(f"-----------------Mission Completed for 'run_backup_process' at {datetime.datetime.now()}------------------")

# ------起動與關閉事件------
@app.on_event("startup")
async def startup_event():
    """啟動排程器並加入任務"""
    # 系統啟動時觸發第一次執行
    #asyncio.create_task(run_tqm_process())
    asyncio.create_task(run_backup_process())
    # 後續的定時任務
    #scheduler.add_job(run_tqm_process, 'interval', minutes=10)
    scheduler.add_job(run_backup_process, 'cron', minute=0)
    scheduler.start()
    print(f"Scheduler started at {datetime.datetime.now()}.")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉排程器"""
    scheduler.shutdown()
    print(f"Scheduler shut down at {datetime.datetime.now()}.")