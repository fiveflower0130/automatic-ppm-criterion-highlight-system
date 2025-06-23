# 只放 MySQL models
from sqlalchemy.schema import Column
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String
from app.database.mysql import mysql_base


class DrillInfo(mysql_base):
    __tablename__ = "lot_drill_result"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(64))
    lot_number = Column(String(32))
    drill_machine_id = Column(Integer)
    drill_machine_name = Column(String(8))
    drill_spindle_id = Column(Integer)
    ppm_control_limit = Column(Integer)
    ppm = Column(Integer)
    judge_ppm = Column(Boolean)
    drill_time = Column(DateTime)
    cpk = Column(Float)
    cp = Column(Float)
    ca = Column(Float)
    aoi_time = Column(DateTime)
    ratio_target = Column(Float)
    image_path = Column(String(128), index=True)
    image_update_time = Column(DateTime)
    classification_result = Column(String(8))
    classification_time = Column(DateTime)
    feedback_result = Column(String(8))
    report_ee = Column(String(16))
    report_time = Column(DateTime)
    comment = Column(String(512))

class MailInfo(mysql_base):
    __tablename__ = "mail_list"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(50))
    send_type = Column(String(10))

class EEInfo(mysql_base):
    __tablename__ = "ee_list"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ee_id = Column(String(10))
    name = Column(String(10))

class PPMArLimitInfo(mysql_base):
    __tablename__ = "ppm_ar_limit"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    ar_level = Column(String(1), primary_key=True, index=True,)
    lower_limit = Column(Float)
    upper_limit = Column(Float)
    ppm_limit = Column(Integer)
    update_time = Column(DateTime)

class PPMCriteriaLimitInfo(mysql_base):
    __tablename__ = "ppm_criteria_limit"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(64), index=True)
    ar = Column(Float)
    ar_level = Column(String(1))
    ppm_limit = Column(Integer)
    modification = Column(Boolean)
    update_time = Column(DateTime)

class FeedbackRecord(mysql_base):
    __tablename__ = "feedback_record"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(64))
    lot_number = Column(String(16))
    drill_machine_name = Column(String(8))
    drill_spindle_id = Column(Integer)
    drill_time = Column(DateTime)
    employee_id = Column(String(8))
    result = Column(String(8))
    comment = Column(String(16))
    update_time = Column(DateTime)

class UserModificationRecord(mysql_base):
    __tablename__ = "user_modification_record"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String(6), index=True)
    sql_command = Column(String(512))
    update_time = Column(DateTime)

class AIPredictionRecord(mysql_base):
    __tablename__ = "prediction_record"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_path = Column(String(128), index=True)
    product_name = Column(String(64))
    classification_code = Column(String(8))
    classification_model = Column(String(32))
    mahalanobis_distance = Column(Float)
    classification_time = Column(DateTime)

class AIClassificationCode(mysql_base):
    __tablename__ = "classification_code"
    __table_args__ = {
        'mysql_engine': 'InnoDB', 
        'mysql_charset': 'utf8mb4', 
        'mysql_collate': 'utf8mb4_unicode_ci', 
        'mysql_row_format': 'DYNAMIC'
    }
    code = Column(String(8), primary_key=True, index=True)
    directions = Column(String(64))

# 若要自動建立資料表，請取消下列註解
# MYSQLBase.metadata.create_all(bind=mysql_engine)
