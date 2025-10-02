import asyncio
import os
import shutil
import datetime
import win32wnet
from win32netcon import RESOURCETYPE_DISK
from dataclasses import dataclass
from icecream import ic
from typing import Optional, List, Dict, Tuple, Any
from app.database import mysql_session
from app.crud import drill as drill_crud, prediction as prediction_crud, mail as mail_crud
from app.utils.data_transfer import DataTransfer
from app.utils.logger import Logger

ic.configureOutput(includeContext=False, contextAbsPath=False)

# 取得logger實例
logger = Logger().get_logger()

class RemoteFolderConnector:
    """遠端資料夾連線器
    使用SMB協議連線到遠端資料夾，要注意的是Windows的防火牆設定可能會阻擋連線，
    參數:
        remote_path: 遠端資料夾路徑, 格式為 \\<IP>\<Folder>
        username: 使用者名稱
        password: 密碼
        domain: 網域
        retry: 連線失敗重試次數, 預設為3
    
    """
    def __init__(self, remote_path, username, password, domain, retry= 3):
        self._remote_path = remote_path
        self._username = username
        self._password = password
        self._domain = domain
        self._retry = retry
        self.connected = False
    
    def connect(self):
        """連線到遠端資料夾"""
        attempt = 0
        net_resource = win32wnet.NETRESOURCE()
        net_resource.lpRemoteName = self._remote_path
        net_resource.dwType = RESOURCETYPE_DISK
        full_username = f"{self._domain}\\{self._username}" if self._domain else self._username
        while attempt < self._retry:
            try:
                win32wnet.WNetAddConnection2(
                    net_resource,
                    self._password,
                    full_username,
                )
                self.connected = True
                logger.info(f"Successfully connected to {self._remote_path}")
                return True
            except Exception as e:
                attempt += 1
                logger.error(f"Attempt {attempt} to connect to {self._remote_path} failed: {e}")
                if attempt >= self._retry:
                    logger.error(f"Failed to connect to {self._remote_path} after {self._retry} attempts due to: {e}")
                    return False
    
    def disconnect(self):
        """斷開與遠端資料夾的連線"""
        if self.connected:
            try:
                win32wnet.WNetCancelConnection2(self._remote_path, 0, True)
                self.connected = False
                logger.info(f"Disconnected from {self._remote_path}")
            except Exception as e:
                logger.error(f"Failed to disconnect from {self._remote_path}: {e}")

@dataclass
class BackupProcessorConfig:
    """備份處理器參數設定"""
    remote_path: str
    dest_path: str
    username: str
    password: str
    domain: str
    retry: int

class BackupProcessor:
    """備份資料處理器
    參數:
        connection_config: BackupProcessorConfig 連線參數設定
        email_client: Any 電子郵件客戶端
        email_host: str 電子郵件主機
    屬性:
        pending_list: List[Tuple[Dict, Dict]] 待處理清單，包含搜尋條件與更新資料
    私有屬性:
        __file_count: int 檔案總數
        __copied_count: int 已複製檔案數
        __db_updated_count: int 已更新資料庫數
    """
    def __init__(self, connection_config: BackupProcessorConfig, email_client: Any, email_host: str):
        # 初始化服務
        self.connection_config = connection_config
        self.email_client = email_client
        self.email_host = email_host
        self.pending_list = []

        self.__file_count = 0
        self.__copied_count = 0
        self.__db_updated_count = 0

    def __parse_filename(self, file_name: str) -> Dict[str, Any]:
        """解析檔案名稱以取得相關資訊"""
        if len(file_name) < 36: return {}
        try:
            # 假設檔案名稱格式為: <timestamp><machine_name><spindle_id><lot_number><target_or_panel>.jpg ex:20250917025100ND08SP6L250910079Panel.jpg
            # 1. 去除副檔名
            name_without_ext = os.path.splitext(file_name)[0]

            # 2. 擷取固定長度資料
            image_create_time = datetime.datetime.strptime(file_name[0:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            machine_name = file_name[14:18]
            spindle_id = file_name[20:21]

            # 3. 判斷長度以擷取Lot與Target/Panel
            remaining_part = name_without_ext[21:]
            target_or_panel = None
            lot_number = None

            if remaining_part.endswith("Target"):
                target_or_panel = remaining_part[-6:]
                lot_number = remaining_part[:-6]
            elif remaining_part.endswith("Panel"):
                target_or_panel = remaining_part[-5:]
                lot_number = remaining_part[:-5]
            else:
                logger.error(f"Invalid file name format: {file_name}")
                return {}
            
            # 4. 回傳結果
            return {
                "image_create_time": image_create_time,
                "machine_name": machine_name,
                "spindle_id": spindle_id,
                "lot_number": lot_number,
                "target_panel": target_or_panel
            }
            
        except Exception as e:
            logger.error(f"Failed to parse file name {file_name}: {e}")
            return {}
        

    async def run_process(self):

        """執行 Drill map Backup 處理流程"""
        start_time = datetime.datetime.now()
        print("------ Drill map Backup 任務處理流程開始 ------")

        # 確認備份資料夾
        os.makedirs(self.connection_config.dest_path, exist_ok=True)
        # 連線到遠端資料夾
        connector = RemoteFolderConnector(
            remote_path=self.connection_config.remote_path,
            username=self.connection_config.username,
            password=self.connection_config.password,
            domain=self.connection_config.domain,
            retry=self.connection_config.retry
        )

        # 備份與更新邏輯
        try:
            # 連線到遠端資料夾，並在獨立執行緒中執行以避免阻塞主線程
            connect_success = await asyncio.to_thread(connector.connect)
            # 1. 判定是否能連線到遠端資料夾
            if not connect_success:
                logger.error("無法連線到遠端資料夾，終止備份任務。")
                # 這裡可以補上寄信通知管理員
                return
            
            # 2. 瀏覽遠端資料夾內容並備份檔案
            async with mysql_session() as mydb:
                for root, dirs, files in os.walk(self.connection_config.remote_path):
                    rel_path = os.path.relpath(root, self.connection_config.remote_path) # 計算相對路徑
                    dest_dir = os.path.join(self.connection_config.dest_path, rel_path) # 目標資料夾
                    os.makedirs(dest_dir, exist_ok=True) # 確保目標資料夾存在
                    ic_message = f"{root} -> {dest_dir}"
                    ic("Processing directory: ", ic_message)
                    
                    for file in files:
                        self.__file_count += 1
                        remote_path = os.path.join(root, file)
                        dest_path = os.path.join(dest_dir, file)
                        if os.path.exists(dest_path):
                            continue
                        try:
                            shutil.copy2(remote_path, dest_path)
                            self.__copied_count += 1
                            ic(f"已備份檔案: {dest_path}")
                        except Exception as e:
                            logger.error(f"Failed to copy file {remote_path} to {dest_path}: {e}")
                            continue

                        # 解析檔案名稱
                        file_info = self.__parse_filename(file)

                        # 確認檔案內容是否需要更新到資料庫
                        if not file_info:
                            continue

                        if file_info["target_panel"] != "Target":
                            logger.warning(f"Skipping non-Target file: {file}")
                            continue

                        # 抓取欲更新資料進行比對
                        search_criteria = {
                            "lot_number": file_info["lot_number"],
                            "machine_name": file_info["machine_name"],
                            "spindle_id": int(file_info["spindle_id"])-1 if isinstance(file_info["spindle_id"], str) else file_info["spindle_id"]-1
                        }
                        ic("search_criteria:", search_criteria)
                        try:
                            records = await drill_crud.get_drill_info_by_image_info(mydb, search_criteria)
                        except Exception as e:
                            logger.error(f"Database query failed for criteria {search_criteria}: {e}")
                            records = []
                        if records:
                            for record in records:
                                if not record.image_path or not record.image_update_time:
                                    search_drill = {
                                        "lot_number": record.lot_number,
                                        "drill_machine_id": record.drill_machine_id,
                                        "drill_spindle_id": record.drill_spindle_id,
                                        "aoi_time": record.aoi_time
                                        }
                                    update_data = {
                                        "image_path": dest_path,
                                        "image_update_time": file_info["image_create_time"]
                                    }
                                    if await drill_crud.update_drill_report_info(mydb, search_drill, update_data):
                                        self.__db_updated_count += 1
                                        logger.info(f"Updated DrillInfo ID {record.id} with image_path {dest_path} and image_update_time {file_info['image_create_time']}")
                                    else:
                                        logger.error(f"Failed to update DrillInfo ID {record.id}, move to the pending area")
                                        self.pending_list.append((search_drill, update_data))
                                else:
                                    ic(f"DrillInfo ID {record.id} already has image_path and image_update_time, skipping update")
                        else: 
                            # 刪除備份檔案
                            try:
                                logger.info(f"No matching Drill Info found for file: {file}, delete the backup file: {dest_path}")
                                os.remove(dest_path)
                                self.__copied_count -= 1
                            except Exception as e:
                                logger.error(f"Failed to delete backup file {dest_path}: {e}")
            
        except Exception as e:
            logger.error(f"備份過程中發生錯誤: {e}")

        finally:
            # 斷開遠端資料夾連線，並在獨立執行緒中執行以避免阻塞主線程
            if connector.connected:
                await asyncio.to_thread(connector.disconnect)
                
            end_time = datetime.datetime.now()
            print(f"------ Drill map Backup 任務處理流程結束，處理數量: {self.__file_count}, 複製圖片:{self.__copied_count}, 更新資料庫:{self.__db_updated_count}，耗時: {end_time - start_time} ------")
            print("Pending list:", self.pending_list)