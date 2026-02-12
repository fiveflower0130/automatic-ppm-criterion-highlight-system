import asyncio
import datetime
from fastapi import FastAPI
# from fastapi_utils.tasks import repeat_every
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from icecream import ic
from app.routes import drill_router, feedback_router, mail_router, ppm_router, user_router
from app.services.email_service import EmailClient
from app.services.tqm_service import TQMProcessorConfig, TQMProcessor
from app.services.backup_service import BackupProcessorConfig, BackupProcessor
from app.config import Config

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

# 初始化 TQM 處理器服務
tqm_processor = TQMProcessor(
    work_config=TQMProcessorConfig(
        max_db_workers=5,
        batch_size=500,
        enable_email=False,
        enable_save=True
    ),
    email_client=email_client,
    email_host=Config.EMAIL_HOST
)
# 初始化 Backup 處理器服務
backup_processor = BackupProcessor(
    connection_config=BackupProcessorConfig(
        remote_path=Config.BACKUP_REMOTE_PATH,
        dest_path=Config.BACKUP_DEST_PATH,
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

# ------設定定時排程任務的異步function------
async def run_tqm_process():
    await tqm_processor.run_process()

async def run_backup_process():
    await backup_processor.run_process()

# ------起動與關閉事件------
@app.on_event("startup")
async def startup_event():
    """啟動排程器並加入任務"""
    # 系統啟動時觸發第一次執行(只有測時時用)
    # asyncio.create_task(run_tqm_process())
    asyncio.create_task(run_backup_process()) 

    # 後續的定時任務
    # scheduler.add_job(run_tqm_process, 'interval', minutes=10) # 10分鐘跑一次
    scheduler.add_job(run_backup_process, 'cron', minute=0) # 1小時跑一次
    scheduler.start()
    print(f"Scheduler started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉排程器"""
    scheduler.shutdown()
    print(f"Scheduler shut down at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")