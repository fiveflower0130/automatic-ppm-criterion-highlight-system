import os
import logging
import datetime


class Singleton:
    """單例模式基類"""
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


class Logger(Singleton):
    """日誌管理類別"""
    _logger = None
    _file_handler = None
    _stream_handler = None

    def __init__(self, log_dir: str = "./log", log_level: int = logging.DEBUG):
        if Logger._logger is None:
            Logger._logger = logging.getLogger(__name__)
            Logger._logger.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s \t [%(levelname)s | %(filename)s | %(funcName)s:%(lineno)s ] -> %(message)s'
            )

            # 建立日誌目錄
            os.makedirs(log_dir, exist_ok=True)
            logname = self._generate_log_filename()

            # 設定檔案日誌處理器
            if Logger._file_handler is None:
                Logger._file_handler = logging.FileHandler(
                    os.path.join(log_dir, f"log_{logname}"),
                    encoding="utf-8",
                    mode="a"
                )
                Logger._file_handler.setFormatter(formatter)
                Logger._logger.addHandler(Logger._file_handler)

            # 設定控制台日誌處理器
            if Logger._stream_handler is None:
                Logger._stream_handler = logging.StreamHandler()
                Logger._stream_handler.setFormatter(formatter)
                Logger._logger.addHandler(Logger._stream_handler)

    def _generate_log_filename(self) -> str:
        """產生日誌檔案名稱"""
        return datetime.datetime.now().strftime("%Y-%m-%d.log")

    def get_logger(self) -> logging.Logger:
        """取得日誌物件"""
        return Logger._logger