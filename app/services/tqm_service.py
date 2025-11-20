import asyncio
import datetime
import orjson
from icecream import ic
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError
from typing import Optional, List, Dict, Tuple, Any
from app.database import mssql_session, mysql_session
from app.crud import tqm as tqm_crud, drill as drill_crud, prediction as prediction_crud, ppm as ppm_crud, mail as mail_crud
from app.utils.data_transfer import DataTransfer
from app.services.prediction_service import get_ai_classification
from app.utils.logger import Logger

ic.configureOutput(includeContext=False, contextAbsPath=False)
logger = Logger().get_logger()

@dataclass
class TQMProcessorConfig:
    """TQM 處理器設定"""
    max_db_workers: int = 5
    batch_size: int = 500
    enable_email: bool = True
    enable_save: bool = True


class TQMProcessor:
    """TQM 資料處理器"""
    
    def __init__(self, work_config: TQMProcessorConfig, email_client:Any, email_host:str):
        # 初始化服務
        self.work_config = work_config or TQMProcessorConfig()
        self.transfer = DataTransfer()
        self.email_client = email_client
        self.email_host = email_host

    @asynccontextmanager
    async def _mssql_executor_context(self):
        """MSSQL 執行緒池上下文管理器"""
        executor = ThreadPoolExecutor(max_workers=self.work_config.max_db_workers)
        
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
    
    async def _send_alert_emails(self, mydb, highlight_list: List[Dict]) -> bool:
        """發送警告郵件"""
        if not highlight_list:
            return True
            
        try:
            mail_list = await mail_crud.get_mail_info(mydb)
            self.email_client.add_client(host=self.email_host)
            
            for highlight_info in highlight_list:
                send_data = self.transfer.get_mail_data(highlight_info, mail_list)
                print(f"準備發送郵件: {send_data}")
                # self.email_client.send_email(host=self.email_host, data=send_data)
                
            print(f"PPM 警告資訊已寄出 ({len(highlight_list)} 封)")
            return True
        
        except Exception as mail_err:
            logger.error(f"郵件發送錯誤: {mail_err}")
            return False
        
        finally:
            self.email_client.delete_client(host=self.email_host)
    
    async def _save_data(self, mydb, insert_data: Dict) -> bool:
        save = True
        if insert_data:
            try:
                await drill_crud.create_drill_info(mydb, insert_data)

            except Exception as sql_err:
                logger.error(f"儲存 drill_info 錯誤: {sql_err}")
                save = False

        return save

    async def _save_batch_data(self, mydb, insert_list: List[Dict]) -> bool:
        """批次儲存資料"""
        save = True
        if insert_list:
            try:
                await drill_crud.create_drill_info_all(mydb, insert_list)
                ic(f"成功儲存 {len(insert_list)} 筆 drill_info")

            except Exception as sql_err:
                logger.error(f"儲存 drill_info 錯誤: {sql_err}")
                save = False

        # if prediction_list:
        #     try:
        #         await prediction_crud.create_prediction_record_all(mydb, prediction_list)
        #         print(f"成功儲存 {len(prediction_list)} 筆 prediction_record")
        #     except Exception as sql_err:
        #         logger.error(f"儲存 prediction_record 錯誤: {sql_err}")
        #         save = False

        return save
    
    async def _get_or_create_product_info(self, product_name: str, lot_number: str, mydb) -> Any:
        """取得或建立產品資訊"""

        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                product_info = await ppm_crud.get_ppm_criteria_limit_info(mydb, product_name)
                
                if not product_info:
                    logger.info(f"產品資訊不存在，開始建立: {product_name}")
                    ppm_ar_value_info = self.transfer.get_ppm_ar_value(lot_number)
                    ppm_ar_value = ppm_ar_value_info.get("ColumnValue_1", 0)
                    ic(f"ppm ar value info: {ppm_ar_value_info},  ppm ar value:{ppm_ar_value}")
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
            
            except OperationalError as db_err:
                error_msg = str(db_err)
                if "Lost connection" in error_msg or "Can't reconnect" in error_msg:
                    logger.warning(f"發生MySQL 連線問題，錯誤: {error_msg}")
                    
                    # ✅ 強制回滾交易
                    try:
                        await mydb.rollback()
                    except:
                        pass  # 忽略rollback錯誤

                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒後重試...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指數退避
                        continue
                    else:
                        logger.error(f"取得產品資訊重試失敗，已達最大重試次數 {max_retries}")
                        raise
                else:
                    logger.error(f"其他資料庫錯誤: {db_err}")
                    raise

            except Exception as e:
                logger.error(f"取得或建立產品資訊錯誤: {e}")
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
    
    async def _perform_ai_prediction(self, drill_info: dict) -> Dict:
        """執行 AI 預測"""
        ai_start_time = datetime.datetime.now()
        
        try:
            # 取得 AI 圖片路徑
            image_path_info = await self.transfer.get_ai_drill_img_path(
                drill_info["lot_number"], drill_info["drill_machine_name"],
                drill_info["drill_spindle_id"], drill_info["drill_time"].strftime("%Y-%m-%d %H:%M:%S")
            )
            image_path = image_path_info.get("local_path")
            if not image_path or not self.transfer.get_image_file_check(image_path):
                return drill_info
            
            image_update_time = self.transfer.get_image_update_time(image_path) if image_path else None
            
            # 呼叫 AI 預測服務
            remote_path = image_path_info.get("remote_path")
            ai_classification_result = await get_ai_classification(
                img_src=  remote_path, 
                product_name=drill_info["product_name"]
            )
            
            ai_end_time = datetime.datetime.now()
            classification_time = ai_end_time.strftime("%Y-%m-%d %H:%M:%S")
            ai_prediction_message = f"圖片:{image_path}, 產品:{drill_info['product_name']}, 時間:{ai_end_time - ai_start_time}"
            # ic(f"AI 預測圖片{image_path}, 產品名稱{drill_info['product_name']}, 時間: {ai_end_time - ai_start_time}")
            ic(ai_prediction_message)

            # # 建立預測資訊
            # prediction_info = {
            #     "image_path": image_path,
            #     "product_name": drill_info["product_name"],
            #     "classification_code": ai_classification_result["classification_code"],
            #     "classification_model": ai_classification_result["classification_model"],
            #     "mahalanobis_distance": ai_classification_result["distance"],
            #     "classification_time": classification_time
            # }
            

            # 更新 drill 資訊，如果classification_code不等於"N/A"或"ERROR"的話就多更新image_path和image_update_time
            drill_info.update({
                "classification_result": ai_classification_result["classification_code"],
                "classification_time": classification_time,
            })

            classification_code = ai_classification_result["classification_code"]
            if classification_code not in ["N/A", "ERROR"]:
                drill_info.update({
                    "image_path": image_path,
                    "image_update_time": image_update_time
                })
            
            return drill_info
            
        except Exception as e:
            logger.error(f"AI 預測失敗: {e}")
            return {}, {}
    
    async def _process_single_board(self, board, mydb, ms_exec) -> Tuple[Dict, Dict]:
        """處理每個 board 資料"""
        try:
            board_id = board.ID_B
            product_id = board.ProductID
            machine_id = board.DrillMachineID
            # print(f"Board info: board_id={board_id}, product_id={product_id}, machine_id={machine_id}")
            
            # 先取得 MSSQL 中所需的資料
            machine_info, measure_info, product_name = await asyncio.gather(
                ms_exec(tqm_crud.get_machine_name, machine_id),
                ms_exec(tqm_crud.get_measure_info, board_id),
                ms_exec(tqm_crud.get_product_name, product_id)
            )

            # 處理產品資訊
            product_info = await self._get_or_create_product_info(product_name, board.Lot, mydb)

            if not (measure_info and machine_info):
                logger.warning(f"警告，此筆資料不完整: board_id={board_id}")
                logger.warning(f"measure_info: {orjson.dumps(measure_info)}")
                logger.warning(f"machine_info: {orjson.dumps(machine_info)}")
                logger.warning(f"product_info: {orjson.dumps(product_info)}")
                return {}, {}

            # 轉換為 drill 資訊
            drill_info = self.transfer.get_drill_info_transfer(board, measure_info, product_info, machine_info)
            
            # 檢查是否已存在 DB
            if await drill_crud.get_drill_info_check(mydb, drill_info):
                logger.info(f"board {board_id} 資料已存在，跳過儲存: , info={drill_info}")
                return {}, {}

            # 執行 AI 預測並加入Drill info
            updated_drill_info = await self._perform_ai_prediction(drill_info)
            
            # 檢查警告條件
            highlight_info = self._check_highlight_condition(updated_drill_info)
            
            return updated_drill_info, highlight_info

        except Exception as e:
            logger.error(f"處理 Board 的資料錯誤: {e}")
            return {}, {}

    async def _get_processing_time_range(self, ms_exec, my_db) -> Tuple[Optional[str], Optional[str]]:
        """
        取得處理時間範圍 (Private)
        確定需要處理的資料時間範圍
        """
        # 取得 TQM 最後一筆 Board 資料
        last_board_info = await ms_exec(tqm_crud.get_board_info_by_last_aoitime)
        if not last_board_info:
            logger.warning("找不到任何TQM Board 的最後一筆資料")
            return None, None
        
        # 取得本地資料庫最後處理時間
        last_drill_info = await drill_crud.get_drill_info_by_last_aoitime(my_db)
            
        if not last_drill_info:
            # 如果本地沒有資料，從TQM第一筆開始處理
            start_time = await self._get_first_board_time(ms_exec)
            if not start_time:
                return None, None
        else:
            start_time = last_drill_info.aoi_time.strftime("%Y/%m/%d %H:%M:%S")
            
        end_time = last_board_info.AOITime
        return start_time, end_time
    
    async def _execute_batch_processing_loop(self, ms_exec, my_db, start_time: str, end_time: str):
        """
        執行批次處理主迴圈 (Private)
        分批處理 Board 資料直到處理完成
        """
        
        while end_time > start_time:
            # 擷取當前批次的 Board 資料
            boards_info = await ms_exec(tqm_crud.get_boards_info_by_datetime, start_time)
            if not boards_info:
                logger.info("沒有找到新的 Board 資料！")
                break
                    
            ic(f"開始處理 {len(boards_info)} 筆 Board 資料")
                
            # 處理當前批次
            processing_result = await self._process_current_batch(ms_exec, my_db, boards_info)
                
            # 發送警告郵件
            await self._handle_alert_emails(my_db, processing_result['highlight_list'])
                
            # 更新下一批次的開始時間
            start_time = boards_info[-1].AOITime
            ic(f"批次處理完成，更新開始時間: {start_time}")

    async def _process_current_batch(self, ms_exec, my_db, boards_info: List) -> Dict[str, Any]:
        """
        處理當前批次的 Board 資料 (Private)
        返回處理結果統計資訊
        """
        highlight_list = []
        save_count = 0
        error_count = 0
        
        for board in boards_info:
            try:
                # 處理單個 Board
                drill_info, highlight_info = await self._process_single_board(board, my_db, ms_exec)
                
                # 處理 drill_info 儲存
                if drill_info and self.work_config.enable_save:
                    if await self._save_data(my_db, drill_info):
                        save_count += 1
                        
                # 收集需要發送警告的資料
                if highlight_info:
                    highlight_list.append(highlight_info)
            
            except OperationalError as db_err:
                if "Lost connection" in str(db_err) or "Can't reconnect" in str(db_err):
                    logger.error(f"MySQL 連線問題，跳過此 Board: {board.ID_B}")
                    error_count += 1
                    continue
                else:
                    raise

            except Exception as e:
                logger.error(f"處理各別需求資訊錯誤: {e}")
                error_count += 1
                continue
        
        ic(f"本批次成功儲存 {save_count} 筆 drill_info 資料，錯誤 {error_count} 筆")
        
        return {
            'highlight_list': highlight_list,
            'save_count': save_count,
            'error_count': error_count,
            'processed_count': len(boards_info)
        }
    
    async def _handle_alert_emails(self, my_db, highlight_list: List[Dict]):
        """
        處理警告郵件發送 (Private)
        根據設定決定是否發送警告郵件
        """
        if self.work_config.enable_email and highlight_list:
            try:
                await self._send_alert_emails(my_db, highlight_list)
            except Exception as email_err:
                logger.error(f"警告郵件處理失敗: {email_err}")
        
    async def run_process(self):
        """執行 TQM 處理流程"""
        print(f"------ 開始 TQM 任務處理流程 {datetime.datetime.now()} ------")
        # 設定開始時間
        start_process_time = datetime.datetime.now()

        try:
            async with self._mssql_executor_context() as ms_exec:
                # 1. 取得TQM抓取的時間範圍
                async with mysql_session() as my_db:
                    start_time, end_time = await self._get_processing_time_range(ms_exec, my_db)
                    if not start_time or not end_time:
                        logger.warning("無法取得有效的時間範圍，跳過本次處理")
                        return
                    logger.info(f"處理機鑽 Board 的時間範圍: {start_time} - {end_time}")

                    # 2. 執行批次處理主迴圈
                    await self._execute_batch_processing_loop(ms_exec, my_db, start_time, end_time)

            # 3. 紀錄結束時間   

                # # 分批處理主迴圈
                # while end_time > start_time:
                #         # 2. 擷取主板資料
                #         boards_info = await ms_exec(tqm_crud.get_boards_info_by_datetime, start_time)
                #         if not boards_info:
                #             logger.info("沒有找到新的 Board 資料！")
                #             break

                #         ic(f"開始處理 {len(boards_info)} 筆 Board 資料")

                #         # 3. 處理各別資料
                #         # insert_list, highlight_list = [], []
                #         highlight_list = []
                #         save_count = 0

                #         for board in boards_info:    
                #             try:
                #                 drill_info, highlight_info = await self._process_single_board(board, mydb, ms_exec)     
                #                 if drill_info:
                #                     # insert_list.append(drill_info)
                #                     if self.work_config.enable_save:
                #                         if await self._save_data(mydb, drill_info):
                #                             save_count += 1

                #                 if highlight_info:
                #                     highlight_list.append(highlight_info)
                                    
                #             except Exception as e:
                #                 logger.error(f"處理各別需求資訊錯誤: {e}")
                #                 continue
                        
                #         ic (f"本批次成功儲存 {save_count} 筆 drill_info 資料")
                #         # 4. 批次儲存資料 - 在呼叫前判斷
                #         # if self.work_config.enable_save:
                #         #     save = await self._save_batch_data(mydb, insert_list)
                           
                #         # 5. 發送警告郵件 - 在呼叫前判斷
                #         if self.work_config.enable_email:
                #             send = await self._send_alert_emails(mydb, highlight_list)
                        
                #         # 更新開始時間
                #         start_time = boards_info[-1].AOITime
                #         ic(f"批次處理完成，更新開始時間: {start_time}")

            end_process_time = datetime.datetime.now()
            processing_time = end_process_time - start_process_time
            print(f"------ 結束 TQM 任務處理流程，總耗時: {processing_time} ------")

        except Exception as e:
            logger.error(f"TQM 任務處理錯誤: {e}")