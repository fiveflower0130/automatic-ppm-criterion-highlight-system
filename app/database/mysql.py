from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from app.config import Config

DATABASE_URL = (
    f"mysql+asyncmy://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}"
    f"@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_ = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
mysql_base = declarative_base()

# 使用 Depends 來取得 MySQL 資料庫連線(用於API呼叫)
async def get_mysql_db():
    async with async_session_() as session:
        yield session

# 使用 asynccontextmanager 來管理 MySQL 資料庫連線(非API呼叫時使用)
@asynccontextmanager
async def mysql_session():
    async for session in get_mysql_db():
        yield session

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from app.config import Config

# # MySQL 資料庫連線設定
# DATABASE_URL = f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"

# engine = create_engine(DATABASE_URL)
# mysql_session_ = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# mysql_base = declarative_base()

# def get_mysql_db():
#     """取得 MySQL 資料庫連線"""
#     db = mysql_session_()
#     try:
#         yield db
#     finally:
#         db.close()