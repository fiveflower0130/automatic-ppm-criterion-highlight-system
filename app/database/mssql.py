from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.config import Config

# MSSQL 資料庫連線設定
DATABASE_URL = (
    f"mssql+pyodbc://{Config.MSSQL_USER}:{Config.MSSQL_PASSWORD}"
    f"@{Config.MSSQL_HOST}:{Config.MSSQL_PORT}/{Config.MSSQL_DB}"
    f"?driver=ODBC+Driver+17+for+SQL+Server"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
mssql_base = declarative_base()

# 使用 Depends 來取得 MSSQL 資料庫連線(用於API呼叫)
def get_mssql_db():
    """取得 MSSQL 資料庫連線"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 使用 contextmanager 來管理 MSSQL 資料庫連線(非API呼叫時使用)
@contextmanager
def mssql_session():
    """MSSQL 資料庫 session 上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker, declarative_base
# from contextlib import asynccontextmanager
# from app.config import Config

# # MSSQL 資料庫連線設定
# DATABASE_URL = (
#     f"mssql+aioodbc://{Config.MSSQL_USER}:{Config.MSSQL_PASSWORD}"
#     f"@{Config.MSSQL_HOST}:{Config.MSSQL_PORT}/{Config.MSSQL_DB}"
#     "?driver=ODBC+Driver+17+for+SQL+Server"
# )
# print(DATABASE_URL)

# engine = create_async_engine(DATABASE_URL, echo=False, future=True)
# async_session_ = sessionmaker(
#     engine, 
#     expire_on_commit=False, 
#     class_=AsyncSession
# )
# mssql_base = declarative_base()

# # 使用Depends來取得 MSSQL 資料庫連線(用於API呼叫)
# async def get_mssql_db():
#     async with async_session_() as session:
#         yield session

# # 使用 asynccontextmanager 來管理 MSSQL 資料庫連線(非API呼叫時使用)
# @asynccontextmanager
# async def mssql_session():
#     async for session in get_mssql_db():
#         yield session





