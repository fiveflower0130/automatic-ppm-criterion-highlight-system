import asyncio
import datetime
import orjson
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Tuple, Any
from app.database import mssql_session, mysql_session
from app.crud import tqm as tqm_crud, drill as drill_crud, prediction as prediction_crud, ppm as ppm_crud, mail as mail_crud
from app.utils.data_transfer import DataTransfer
from app.services.email_service import EmailClient
from app.services.prediction_service import get_ai_classification
from app.config import Config
from app.utils.logger import Logger

@dataclass
class TQMProcessorConfig:
    """TQM 處理器設定"""
    max_db_workers: int = 5
    batch_size: int = 500
    enable_email: bool = True
    enable_save: bool = True


class TQMProcessor:
    """TQM 資料處理器"""
    
    def __init__(self, config: Optional[TQMProcessorConfig] = None):
        self.config = config or TQMProcessorConfig()
        
        # 初始化服務
        self.logger = Logger().get_logger()
        self.transfer = DataTransfer()
        self.email_client = EmailClient()
        self.email_host = Config.EMAIL_HOST
    
    @asynccontextmanager
    async def _mssql_executor_context(self):
        """MSSQL 執行緒池上下文管理器"""
        executor = ThreadPoolExecutor(max_workers=self.config.max_db_workers)
        
        def sync_operation(operation_func, *args, **kwargs):
            with mssql_session() as db:
                return operation_func(db, *args, **kwargs)
        
        async def async_operation(operation_func, *args, **kwargs):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(executor, sync_operation, operation_func, *args, **kwargs)
        
        try:
            yield async_operation
        finally:
            executor.shutdown(wait=True)
            # self.logger.debug("MSSQL 執行緒池已關閉")
    
    async def _send_alert_emails(self, mydb, highlight_list: List[Dict]) -> bool:
        """發送警告郵件"""
        if not highlight_list:
            return True
            
        try:
            mail_list = await mail_crud.get_mail_info(mydb)
            self.email_client.add_client(host=self.email_host)
            
            for highlight_info in highlight_list:
                send_data = self.transfer.get_mail_data(highlight_info, mail_list)
                self.logger.info(f"準備發送郵件: {send_data}")
                # self.email_client.send_email(host=self.email_host, data=send_data)
                
            self.logger.info(f"PPM 警告資訊已寄出 ({len(highlight_list)} 封)")
            return True
        except Exception as mail_err:
            self.logger.error(f"郵件發送錯誤: {mail_err}")
            return False
        finally:
            self.email_client.delete_client(host=self.email_host)
    
    async def _save_batch_data(self, mydb, prediction_list: List[Dict], insert_list: List[Dict]) -> bool:
        """批次儲存資料"""
        save = True
        if insert_list:
            try:
                await drill_crud.create_drill_info_all(mydb, insert_list)
                self.logger.info(f"成功儲存 {len(insert_list)} 筆 drill_info")
            except Exception as sql_err:
                self.logger.error(f"儲存 drill_info 錯誤: {sql_err}")
                save = False

        if prediction_list:
            try:
                await prediction_crud.create_prediction_record_all(mydb, prediction_list)
                self.logger.info(f"成功儲存 {len(prediction_list)} 筆 prediction_record")
            except Exception as sql_err:
                self.logger.error(f"儲存 prediction_record 錯誤: {sql_err}")
                save = False

        return save
    
    async def _get_or_create_product_info(self, product_name: str, lot_number: str, mydb) -> Any:
        """取得或建立產品資訊"""
        try:
            product_info = await ppm_crud.get_ppm_criteria_limit_info(mydb, product_name)
            
            if not product_info:
                self.logger.info(f"產品資訊不存在，開始建立: {product_name}")
                ppm_ar_value = await self.transfer.get_ppm_ar_value(lot_number)
                if ppm_ar_value:
                    ppm_ar_limit_info = await ppm_crud.get_ppm_ar_limit_info(mydb)
                    ppm_criteria_limit_info = await self.transfer.get_ppm_criteria_limit_info(
                        product_name=product_name, ar_value=ppm_ar_value, ar_info=ppm_ar_limit_info
                    )
                    product_info = await ppm_crud.create_ppm_criteria_limit_info(mydb, ppm_criteria_limit_info)
                else:
                    class ProductInfo:
                        def __init__(self, product_name):
                            self.product_name = product_name
                            self.ppm_limit = None
                    product_info = ProductInfo(product_name)
            
            return product_info
        except Exception as e:
            self.logger.error(f"取得或建立產品資訊錯誤: {e}")
            raise
    
    def _check_highlight_condition(self, drill_info: dict) -> dict:
        """檢查是否需要發送警告"""
        if (not drill_info.get("judge_ppm") and 
            drill_info.get("ppm_control_limit", 0) > 0 and 
            drill_info.get("ratio_target", 0) > 0):
            
            return {
                "machine_name": drill_info["drill_machine_name"],
                "spindle_id": drill_info["drill_spindle_id"],
                "lot_number": drill_info["lot_number"],
                "ppm": drill_info["ppm"],
                "ppm_control_limit": drill_info["ppm_control_limit"]
            }
        return {}
    
    async def _perform_ai_prediction(self, drill_info: dict) -> Tuple[Dict, Dict]:
        """執行 AI 預測"""
        ai_start_time = datetime.datetime.now()
        
        try:
            # 取得 AI 圖片路徑
            ai_image_path = await self.transfer.get_ai_drill_img_path(
                drill_info["lot_number"], drill_info["drill_machine_name"],
                drill_info["drill_spindle_id"], drill_info["drill_time"].strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # 呼叫 AI 預測服務
            ai_classification_result = await get_ai_classification(
                img_src=ai_image_path, 
                product_name=drill_info["product_name"]
            )
            
            ai_end_time = datetime.datetime.now()
            classification_time = ai_end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"AI 預測時間: {ai_end_time - ai_start_time}")
            
            # 建立預測資訊
            prediction_info = {
                "image_path": ai_image_path,
                "product_name": drill_info["product_name"],
                "classification_code": ai_classification_result["classification_code"],
                "classification_model": ai_classification_result["classification_model"],
                "mahalanobis_distance": ai_classification_result["distance"],
                "classification_time": classification_time
            }
            
            # 更新 drill 資訊
            drill_info.update({
                "classification_result": ai_classification_result["classification_code"],
                "classification_time": classification_time,
                "image_path": ai_image_path
            })
            
            return prediction_info, drill_info
            
        except Exception as e:
            self.logger.error(f"AI 預測失敗: {e}")
            return {}, {}
    
    async def _process_single_board(self, board, mydb, ms_exec) -> Tuple[Dict, Dict, Dict]:
        """處理每個 board 資料"""
        try:
            board_id = board.ID_B
            product_id = board.ProductID
            machine_id = board.DrillMachineID
            print(f"Board info: board_id={board_id}, product_id={product_id}, machine_id={machine_id}")
            
            # 先取得 MSSQL 中所需的資料
            machine_info, measure_info, product_name = await asyncio.gather(
                ms_exec(tqm_crud.get_machine_name, machine_id),
                ms_exec(tqm_crud.get_measure_info, board_id),
                ms_exec(tqm_crud.get_product_name, product_id)
            )

            # 處理產品資訊
            product_info = await self._get_or_create_product_info(product_name, board.Lot, mydb)

            if not (measure_info and machine_info):
                self.logger.warning(f"警告，此筆資料不完整: board_id={board_id}")
                self.logger.warning(f"measure_info: {orjson.dumps(measure_info)}")
                self.logger.warning(f"machine_info: {orjson.dumps(machine_info)}")
                self.logger.warning(f"product_info: {orjson.dumps(product_info)}")
                return {}, {}, {}

            # 轉換為 drill 資訊
            drill_info = self.transfer.get_drill_info_transfer(board, measure_info, product_info, machine_info)
            
            # 檢查是否已存在 DB
            if await drill_crud.get_drill_info_check(mydb, drill_info):
                return {}, {}, {}

            # 執行 AI 預測
            prediction_info, updated_drill_info = await self._perform_ai_prediction(drill_info)
            
            # 檢查警告條件
            highlight_info = self._check_highlight_condition(updated_drill_info)
            
            return prediction_info, updated_drill_info, highlight_info

        except Exception as e:
            self.logger.error(f"處理 Board 的資料錯誤: {e}")
            return {}, {}, {}
        
    async def run_process(self):
        """執行 TQM 處理流程"""
        self.logger.info("=== 開始 TQM 任務處理流程 ===")
        # 設定開始時間
        start_process_time = datetime.datetime.now()
        try:
            async with self._mssql_executor_context() as ms_exec:
                # 1. 取得時間範圍
                last_board_info = await ms_exec(tqm_crud.get_board_info_by_last_aoitime)

                async with mysql_session() as mydb:
                    last_drill_info = await drill_crud.get_drill_info_by_last_aoitime(mydb)
                    
                    if not last_drill_info:
                        first_board_info = await ms_exec(tqm_crud.get_board_info_by_first_aoitime)
                        start_time = first_board_info.AOITime if first_board_info else None
                        if not start_time:
                            self.logger.warning("找不到任何 Board 資料")
                            return
                    else:
                        start_time = last_drill_info.aoi_time.strftime("%Y/%m/%d %H:%M:%S")
                    
                    end_time = last_board_info.AOITime
                    self.logger.info(f"處理機鑽 Board 的時間範圍: {start_time} - {end_time}")

                    # 分批處理主迴圈
                    while end_time > start_time:
                        # 2. 擷取主板資料
                        boards_info = await ms_exec(tqm_crud.get_boards_info_by_datetime, start_time)
                        if not boards_info:
                            self.logger.info("沒有找到新的 Board 資料！")
                            break

                        self.logger.info(f"開始處理 {len(boards_info)} 筆 Board 資料")

                        # 3. 處理各別資料
                        prediction_list, insert_list, highlight_list = [], [], []

                        for board in boards_info:
                            try:
                                prediction_info, drill_info, highlight_info = await self._process_single_board(board, mydb, ms_exec)
                                
                                if prediction_info:
                                    prediction_list.append(prediction_info)
                                if drill_info:
                                    insert_list.append(drill_info)
                                if highlight_info:
                                    highlight_list.append(highlight_info)
                                    
                            except Exception as e:
                                self.logger.error(f"處理各別需求資訊錯誤: {e}")
                                continue
                        
                        # 4. 批次儲存資料 - 在呼叫前判斷
                        if self.config.enable_save:
                            await self._save_batch_data(mydb, prediction_list, insert_list)
                        
                        # 5. 發送警告郵件 - 在呼叫前判斷
                        if self.config.enable_email:
                            await self._send_alert_emails(mydb, highlight_list)

                        # 更新開始時間
                        start_time = boards_info[-1].AOITime
                        self.logger.info(f"批次處理完成，更新開始時間: {start_time}")

            end_process_time = datetime.datetime.now()
            processing_time = end_process_time - start_process_time
            self.logger.info(f"=== TQM 處理流程完成，總耗時: {processing_time} ===")

        except Exception as e:
            self.logger.error(f"TQM 任務處理錯誤: {e}")
            raise


# # 初始化模組
# logger = Logger().get_logger()
# transfer = DataTransfer()
# email_client = EmailClient()
# email_host = Config.EMAIL_HOST


# @asynccontextmanager
# async def mssql_executor_context(max_workers: int = 5):
#     """MSSQL 執行緒池上下文管理器"""
#     executor = ThreadPoolExecutor(max_workers=max_workers)
    
#     def sync_operation(operation_func, *args, **kwargs):
#         """同步執行 MSSQL 操作"""
#         with mssql_session() as db:
#             return operation_func(db, *args, **kwargs)
    
#     async def async_operation(operation_func, *args, **kwargs):
#         """異步包裝 MSSQL 操作"""
#         loop = asyncio.get_event_loop()
#         return await loop.run_in_executor(executor, sync_operation, operation_func, *args, **kwargs)
    
#     try:
#         yield async_operation
#     finally:
#         executor.shutdown(wait=True)
#         # logger.debug("MSSQL 執行緒池已關閉")

# async def send_alert_emails(mydb, highlight_list: List[Dict]) -> bool:
#     """發送警告郵件"""
#     if not highlight_list:
#         return True
        
#     try:
#         mail_list = await mail_crud.get_mail_info(mydb)
#         email_client.add_client(host=email_host)
        
#         for highlight_info in highlight_list:
#             send_data = transfer.get_mail_data(highlight_info, mail_list)
#             logger.info(f"準備發送郵件: {send_data}")
#             # email_client.send_email(host=email_host, data=send_data)
            
#         logger.info(f"PPM 警告資訊已寄出 ({len(highlight_list)} 封)")
#         return True
#     except Exception as mail_err:
#         logger.error(f"郵件發送錯誤: {mail_err}")
#         return False
#     finally:
#         email_client.delete_client(host=email_host)

# async def save_batch_data(mydb, prediction_list: List[Dict], insert_list: List[Dict]) -> bool:
#     """批次儲存資料"""
#     save = True
#     if insert_list:
#         try:
#             await drill_crud.create_drill_info_all(mydb, insert_list)
#         except Exception as sql_err:
#             logger.error(f"儲存 drill_info 錯誤: {sql_err}")
#             save = False

#     if prediction_list:
#         try:
#             await prediction_crud.create_prediction_record_all(mydb, prediction_list)
#         except Exception as sql_err:
#             logger.error(f"儲存 prediction_record 錯誤: {sql_err}")
#             save = False

#     return save

# async def get_or_create_product_info(product_name: str, lot_number: str, mydb) -> Any:
#     """取得或建立產品資訊"""
#     try:
#         product_info = await ppm_crud.get_ppm_criteria_limit_info(mydb, product_name)
        
#         if not product_info:
#             logger.info(f"產品資訊不存在，開始建立: {product_name}")
#             ppm_ar_value = await transfer.get_ppm_ar_value(lot_number)
#             if ppm_ar_value:
#                 ppm_ar_limit_info = await ppm_crud.get_ppm_ar_limit_info(mydb)
#                 ppm_criteria_limit_info = await transfer.get_ppm_criteria_limit_info(
#                     product_name=product_name, ar_value=ppm_ar_value, ar_info=ppm_ar_limit_info
#                 )
#                 product_info = await ppm_crud.create_ppm_criteria_limit_info(mydb, ppm_criteria_limit_info)
#             else:
#                 # 建立預設產品資訊
#                 class ProductInfo:
#                     def __init__(self, product_name):
#                         self.product_name = product_name
#                         self.ppm_limit = None
#                 product_info = ProductInfo(product_name)
        
#         return product_info
#     except Exception as e:
#         logger.error(f"取得或建立產品資訊錯誤: {e}")
#         raise e

# def check_highlight_condition(drill_info:dict) -> dict:
#     """檢查是否需要發送警告"""
#     if (not drill_info.get("judge_ppm") and 
#         drill_info.get("ppm_control_limit", 0) > 0 and 
#         drill_info.get("ratio_target", 0) > 0):
        
#         return {
#             "machine_name": drill_info["drill_machine_name"],
#             "spindle_id": drill_info["drill_spindle_id"],
#             "lot_number": drill_info["lot_number"],
#             "ppm": drill_info["ppm"],
#             "ppm_control_limit": drill_info["ppm_control_limit"]
#         }
#     return {}

# async def perform_ai_prediction(drill_info: dict) -> Tuple[Dict, Dict]:
#     """執行 AI 預測"""
#     ai_start_time = datetime.datetime.now()
    
#     # 取得 AI 圖片路徑
#     ai_image_path = await transfer.get_ai_drill_img_path(
#         drill_info["lot_number"], drill_info["drill_machine_name"],
#         drill_info["drill_spindle_id"], drill_info["drill_time"].strftime("%Y-%m-%d %H:%M:%S")
#     )
    
#     # 呼叫 AI 預測服務
#     ai_classification_result = await get_ai_classification(
#         img_src=ai_image_path, 
#         product_name=drill_info["product_name"]
#     )
    
#     ai_end_time = datetime.datetime.now()
#     classification_time = ai_end_time.strftime("%Y-%m-%d %H:%M:%S")
    
#     print(f"AI 預測時間: {ai_end_time - ai_start_time}")
    
#     # 建立預測資訊
#     prediction_info = {
#         "image_path": ai_image_path,
#         "product_name": drill_info["product_name"],
#         "classification_code": ai_classification_result["classification_code"],
#         "classification_model": ai_classification_result["classification_model"],
#         "mahalanobis_distance": ai_classification_result["distance"],
#         "classification_time": classification_time
#     }
    
#     # 更新 drill 資訊
#     drill_info.update({
#         "classification_result": ai_classification_result["classification_code"],
#         "classification_time": classification_time,
#         "image_path": ai_image_path
#     })
    
#     return prediction_info, drill_info

# async def process_single_board(board, mydb, ms_exec):
#     """處理每個board資料"""
#     try:
#         board_id = board.ID_B
#         product_id = board.ProductID
#         machine_id = board.DrillMachineID
#         print(f"Board info: board_id={board_id}, product_id={product_id}, machine_id={machine_id}")
#         # 先取得 MSSQL 中所需的資料
#         machine_info, measure_info, product_name = await asyncio.gather(
#             ms_exec(tqm_crud.get_machine_name, machine_id),
#             ms_exec(tqm_crud.get_measure_info, board_id),
#             ms_exec(tqm_crud.get_product_name, product_id)
#         )

#         # 處理產品資訊
#         product_info = await get_or_create_product_info(product_name, board.Lot, mydb)

#         if not (measure_info and machine_info):
#             logger.warning(f"警告，此筆資料不完整: board_id={board_id}")
#             logger.warning(f"measure_info: {orjson.dumps(measure_info)}")
#             logger.warning(f"machine_info: {orjson.dumps(machine_info)}")
#             logger.warning(f"product_info: {orjson.dumps(product_info)}")
#             return {}, {}, {}

#         # 轉換為 drill 資訊
#         drill_info = transfer.get_drill_info_transfer(board, measure_info, product_info, machine_info)
        
#         # 檢查是否已存在DB
#         if await drill_crud.get_drill_info_check(mydb, drill_info):
#             return {}, {}, {}

#         # 執行 AI 預測
#         prediction_info, updated_drill_info = await perform_ai_prediction(drill_info)
        
#         # 檢查警告條件
#         highlight_info = check_highlight_condition(updated_drill_info)
        
#         return prediction_info, updated_drill_info, highlight_info

#     except Exception as e:
#         logger.error(f"處理Board的資料錯誤: {e}")
#         return {}, {}, {}