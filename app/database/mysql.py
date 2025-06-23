from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import Config

# MySQL 資料庫連線設定
DATABASE_URL = f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"

engine = create_engine(DATABASE_URL)
mysql_session_ = sessionmaker(autocommit=False, autoflush=False, bind=engine)
mysql_base = declarative_base()

def get_mysql_db():
    """取得 MySQL 資料庫連線"""
    db = mysql_session_()
    try:
        yield db
    finally:
        db.close()