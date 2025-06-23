from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import Config

# MSSQL 資料庫連線設定
DATABASE_URL = f"mssql+pyodbc://{Config.MSSQL_USER}:{Config.MSSQL_PASSWORD}@{Config.MSSQL_HOST}:{Config.MSSQL_PORT}/{Config.MSSQL_DB}?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL)
mssql_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
mssql_base = declarative_base()

def get_mssql_db():
    """取得 MSSQL 資料庫連線"""
    db = mssql_session()
    try:
        yield db
    finally:
        db.close()