import os
from dotenv import load_dotenv

# Init loading dotenv
load_dotenv(override=True)

class Config:
    """Configuration class for the application."""
    # General settings
    SOAP_URL = "http://10.12.20.216/mtlserviceproxy/serviceproxy.asmx"
    
    MSSQL_HOST = os.getenv("MSSQL_HOST", "localhost")
    MSSQL_PORT = os.getenv("MSSQL_PORT", "1433")
    MSSQL_USER = os.getenv("MSSQL_USER", "sa")
    MSSQL_PASSWORD = os.getenv("MSSQL_PASSWORD", "password")
    MSSQL_DB = os.getenv("MSSQL_DB", "database")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB = os.getenv("MYSQL_DB", "database")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)