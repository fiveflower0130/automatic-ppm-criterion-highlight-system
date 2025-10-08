import os
from dotenv import load_dotenv

# 載入 .env 文件
load_dotenv()

class Config:
    # Database 設定
    MSSQL_USER = os.getenv("MSSQL_USER", "sa")
    MSSQL_PASSWORD = os.getenv("MSSQL_PASSWORD", "mvtqmsystem")
    MSSQL_HOST = os.getenv("MSSQL_HOST", "10.16.94.44")
    MSSQL_PORT = os.getenv("MSSQL_PORT", "1433")
    MSSQL_DB = os.getenv("MSSQL_DB", "mvTQMBox")

    MYSQL_USER = os.getenv("MYSQL_USER", "5940")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "5940")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB = os.getenv("MYSQL_DB", "tid_5940")

    # Redis 設定
    REDIS_HOST = os.getenv("REDIS_HOST", "192.168.0.107")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "5940")

    # Email 設定
    EMAIL_HOST = os.getenv("EMAIL_HOST", "10.12.10.31")
    EMAIL_PORT = os.getenv("EMAIL_PORT", "")

    # Excel 設定
    PPM_FILE_NAME = os.getenv("PPM_FILE_NAME", "ppm_criteria_limit_20230213_(Security C).xlsx")

    # Webside 設定
    WEBSIDE_HOST = os.getenv("WEB_HOST", "10.16.92.65")
    WEBSIDE_PORT = os.getenv("WEB_PORT", "5940")

    # Image 設定
    DRILL_IMG_FOLDER = os.getenv("DRILL_IMG_FOLDER", "")

    # SOAP 設定
    SOAP_URL = os.getenv("SOAP_URL", "http://10.12.20.216/mtlserviceproxy/serviceproxy.asmx")

    # AI Prediction Service 設定
    AI_SERVICE_HOST = os.getenv("AI_SERVICE_HOST", "192.168.0.107")
    AI_SERVICE_PORT = os.getenv("AI_SERVICE_PORT", "8009")

    # Backup 設定
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    BACKUP_REMOTE_PATH = os.getenv("BACKUP_REMOTE_PATH", "")
    BACKUP_DEST_PATH = os.getenv("BACKUP_DEST_PATH", "D:\\drill_map_backup")
    BACKUP_AD_ACCOUNT = os.getenv("BACKUP_AD_ACCOUNT", "")
    BACKUP_AD_PASSWORD = os.getenv("BACKUP_AD_PASSWORD", "")
    BACKUP_AD_DOMAIN = os.getenv("BACKUP_AD_DOMAIN", "")
    BACKUP_RETRY_TIMES = int(os.getenv("BACKUP_RETRY_TIMES", "3"))