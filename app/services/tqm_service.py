import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor
from app.database import mssql_session, mysql_session
from app.crud import tqm as tqm_crud, drill as drill_crud, prediction as prediction_crud, ppm as ppm_crud, mail as mail_crud
from app.utils.data_transfer import DataTransfer
from app.services.email_service import EmailClient
from app.services.prediction_service import get_ai_classification
from app.config import Config
from app.utils.logger import Logger

# 初始化模組
logger = Logger().get_logger()
transfer = DataTransfer()
email_client = EmailClient()
email_host = Config.EMAIL_HOST

# 使用執行緒池處理 MSSQL 同步操作
executor = ThreadPoolExecutor(max_workers=5)

def sync_mssql_operation(operation_func, *args, **kwargs):
    """同步執行 MSSQL 操作"""
    with mssql_session() as db:
        return operation_func(db, *args, **kwargs)

async def async_mssql_operation(operation_func, *args, **kwargs):
    """異步包裝 MSSQL 操作"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_mssql_operation, operation_func, *args, **kwargs)

async def send_alert_emails(mydb, highlight_list):
    """發送警告郵件"""
    if not highlight_list:
        return
        
    try:
        mail_list = await mail_crud.get_mail_info(mydb)
        email_client.add_client(host=email_host)
        
        for highlight_info in highlight_list:
            send_data = transfer.get_mail_data(highlight_info, mail_list)
            logger.info(f"準備發送郵件: {send_data}")
            # email_client.send_email(host=email_host, data=send_data)
            
        logger.info(f"PPM 警告資訊已寄出 ({len(highlight_list)} 封)")
    except Exception as mail_err:
        logger.error(f"郵件發送錯誤: {mail_err}")
    finally:
        email_client.delete_client(host=email_host)

async def save_batch_data(mydb, prediction_list, insert_list):
    """批次儲存資料"""
    if insert_list:
        try:
            await drill_crud.create_drill_info_all(mydb, insert_list)
            logger.info(f"成功儲存 {len(insert_list)} 筆 drill 資訊")
        except Exception as sql_err:
            logger.error(f"儲存 drill_info 錯誤: {sql_err}")

    if prediction_list:
        try:
            await prediction_crud.create_prediction_record_all(mydb, prediction_list)
            logger.info(f"成功儲存 {len(prediction_list)} 筆預測記錄")
        except Exception as sql_err:
            logger.error(f"儲存 prediction_record 錯誤: {sql_err}")


async def get_or_create_product_info(product_name, lot_number, mydb):
    """取得或建立產品資訊"""
    product_info = await ppm_crud.get_ppm_criteria_limit_info(mydb, product_name)
    
    if not product_info:
        ppm_ar_value = await transfer.get_ppm_ar_value(lot_number)
        if ppm_ar_value:
            ppm_ar_limit_info = await ppm_crud.get_ppm_ar_limit_info(mydb)
            ppm_criteria_limit_info = await transfer.get_ppm_criteria_limit_info(
                product_name=product_name, ar_value=ppm_ar_value, ar_info=ppm_ar_limit_info
            )
            product_info = await ppm_crud.create_ppm_criteria_limit_info(mydb, ppm_criteria_limit_info)
        else:
            # 建立預設產品資訊
            class ProductInfo:
                def __init__(self, product_name):
                    self.product_name = product_name
                    self.ppm_limit = None
            product_info = ProductInfo(product_name)
    
    return product_info

def check_highlight_condition(drill_info):
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
    return None

async def perform_ai_prediction(drill_info):
    """執行 AI 預測"""
    ai_start_time = datetime.datetime.now()
    
    # 取得 AI 圖片路徑
    ai_image_path = await transfer.get_ai_drill_img_path(
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

async def process_single_board(board, mydb):
    """處理單個板子資料"""
    try:
        board_id = board.ID_B
        product_id = board.ProductID
        machine_id = board.DrillMachineID
        print(f"處理板子: board_id={board_id}, product_id={product_id}, machine_id={machine_id}")
        # 先取得 MSSQL 中所需的資料
        machine_info, measure_info, product_name = await asyncio.gather(
            async_mssql_operation(tqm_crud.get_machine_name, machine_id),
            async_mssql_operation(tqm_crud.get_measure_info, board_id),
            async_mssql_operation(tqm_crud.get_product_name, product_id)
        )

        if not (measure_info and machine_info):
            logger.warning(f"資料不完整，跳過處理: board_id={board_id}")
            return None, None, None

        # 處理產品資訊
        product_info = await get_or_create_product_info(product_name, board.Lot, mydb)
        
        # 轉換為 drill 資訊
        drill_info = transfer.get_drill_info_transfer(board, measure_info, product_info, machine_info)
        
        # 檢查是否已存在DB
        if await drill_crud.get_drill_info_check(mydb, drill_info):
            return None, None, None

        # 執行 AI 預測
        prediction_info, updated_drill_info = await perform_ai_prediction(drill_info)
        
        # 檢查警告條件
        highlight_info = check_highlight_condition(updated_drill_info)
        
        return prediction_info, updated_drill_info, highlight_info

    except Exception as e:
        logger.error(f"處理板子資料錯誤: {e}")
        return None, None, None

async def run_tqm_process():
    # 1. 取得時間範圍
    last_board_info = await async_mssql_operation(tqm_crud.get_board_info_by_last_aoitime)

    async with mysql_session() as mydb:
        last_drill_info = await drill_crud.get_drill_info_by_last_aoitime(mydb)
        
        if not last_drill_info:
            first_board_info = await async_mssql_operation(tqm_crud.get_board_info_by_first_aoitime)
            start_time = first_board_info.AOITime
        else:
            start_time = last_drill_info.aoi_time.strftime("%Y/%m/%d %H:%M:%S")
        
        end_time = last_board_info.AOITime
        logger.info(f"處理時間範圍: {start_time} - {end_time}")

         # 分批處理主迴圈
        while end_time > start_time:
            # 2. 擷取主板資料
            boards_info = await async_mssql_operation(tqm_crud.get_boards_info_by_datetime, start_time)
            if not boards_info:
                logger.info("沒有找到新的板子資料，處理完成！")
                break

            # 3. 擷取各別所需資料
            prediction_list, insert_list, highlight_list = [], [], []

            for board in boards_info:
                try:
                    # 處理各別資訊
                    prediction_info, drill_info, highlight_info = await process_single_board(board, mydb)
                    
                    if prediction_info:
                        prediction_list.append(prediction_info)
                    if drill_info:
                        insert_list.append(drill_info)
                    if highlight_info:
                        highlight_list.append(highlight_info)
                        
                except Exception as e:
                    logger.error(f"處理各別需求資訊錯誤: {e}")
                    continue
            
            # 4. 批次儲存資料
            await save_batch_data(mydb, prediction_list, insert_list)
            
            # 5. 發送警告郵件
            await send_alert_emails(mydb, highlight_list)

            # 更新開始時間
            start_time = boards_info[-1].AOITime
            logger.info(f"更新開始時間: {start_time}")

    logger.info(f"TQM 處理完成：{datetime.datetime.now()}")
    
# async def run_tqm_process_brfore():
#     # 取得 session
#     with mssql_session() as msdb:
#         last_board_info = tqm_crud.get_board_info_by_last_aoitime(msdb)
#     async with mysql_session() as mydb:
#         last_drill_info = await drill_crud.get_drill_info_by_last_aoitime(mydb)
#         if not last_drill_info:
#             last_drill_info = await tqm_crud.get_board_info_by_first_aoitime(msdb)
#             start_time = last_drill_info.AOITime
#         else:
#             start_time = last_drill_info.aoi_time.strftime("%Y/%m/%d %H:%M:%S")
#         end_time = last_board_info.AOITime

#         logger.info(f"start_time: {start_time}, end_time: {end_time}")

#         while end_time > start_time:
#             boards_info = await tqm_crud.get_boards_info_by_datetime(msdb, start_time)
#             if not boards_info:
#                 logger.info("No boards_info found, mission completed!")
#                 break

#             prediction_list, insert_list, highlight_list = [], [], []

#             for board in boards_info:
#                 try:
#                     board_id = board.ID_B
#                     product_id = board.ProductID
#                     machine_id = board.DrillMachineID

#                     machine_info = await tqm_crud.get_machine_name(msdb, machine_id)
#                     measure_info = await tqm_crud.get_measure_info(msdb, board_id)
#                     product_name = await tqm_crud.get_product_name(msdb, product_id)
#                     product_info = await ppm_crud.get_ppm_criteria_limit_info(mydb, product_name)

#                     if measure_info and machine_info:
#                         if not product_info:
#                             ppm_ar_value = await transfer.get_ppm_ar_value(board.Lot)
#                             if ppm_ar_value:
#                                 ppm_ar_limit_info = await ppm_crud.get_ppm_ar_limit_info(mydb)
#                                 ppm_criteria_limit_info = await transfer.get_ppm_criteria_limit_info(
#                                     product_name=product_name, ar_value=ppm_ar_value, ar_info=ppm_ar_limit_info
#                                 )
#                                 product_info = await ppm_crud.create_ppm_criteria_limit_info(mydb, ppm_criteria_limit_info)
#                             else:
#                                 class ProductInfo:
#                                     def __init__(self, product_name):
#                                         self.product_name = product_name
#                                         self.ppm_limit = None
#                                 product_info = ProductInfo(product_name)

#                         drill_info = transfer.get_drill_info_transfer(board, measure_info, product_info, machine_info)
#                         check_drill_info_exist = await drill_crud.get_drill_info_check(mydb, drill_info)

#                         if not check_drill_info_exist:
#                             ai_start_time = datetime.datetime.now()
#                             ai_image_path = await transfer.get_ai_drill_img_path(
#                                 drill_info["lot_number"], drill_info["drill_machine_name"],
#                                 drill_info["drill_spindle_id"], drill_info["drill_time"].strftime("%Y-%m-%d %H:%M:%S")
#                             )
#                             # 呼叫AI Predcition Servivce
#                             ai_classification_result = await get_ai_classification(
#                                 img_src=ai_image_path, 
#                                 product_name=drill_info["product_name"]
#                             )
#                             ai_end_time = datetime.datetime.now()
#                             classification_time = ai_end_time.strftime("%Y-%m-%d %H:%M:%S")
#                             print(f"AI Prediction Time:{ai_end_time - ai_start_time}")
#                             prediction_info = {
#                                 "image_path": ai_image_path,
#                                 "product_name": drill_info["product_name"],
#                                 "classification_code": ai_classification_result["classification_code"],
#                                 "classification_model": ai_classification_result["classification_model"],
#                                 "mahalanobis_distance": ai_classification_result["distance"],
#                                 "classification_time": classification_time
#                             }
#                             drill_info.update({
#                                 "classification_result": ai_classification_result["classification_code"],
#                                 "classification_time": classification_time,
#                                 "image_path": ai_image_path
#                             })

#                             prediction_list.append(prediction_info)
#                             insert_list.append(drill_info)

#                             if (not drill_info["judge_ppm"] and drill_info["ppm_control_limit"] > 0 and drill_info["ratio_target"] > 0):
#                                 highlight_info = {
#                                     "machine_name": drill_info["drill_machine_name"],
#                                     "spindle_id": drill_info["drill_spindle_id"],
#                                     "lot_number": drill_info["lot_number"],
#                                     "ppm": drill_info["ppm"],
#                                     "ppm_control_limit": drill_info["ppm_control_limit"]
#                                 }
#                                 highlight_list.append(highlight_info)
#                     else:
#                         logger.warning(f"資料不完整: board={board}, measure_info={measure_info}, machine_info={machine_info}, product_info={product_info}")

#                 except Exception as trans_err:
#                     logger.error(f"資料轉換錯誤: {trans_err}")
#                     continue

#             if insert_list:
#                 try:
#                     await drill_crud.create_drill_info_all(mydb, insert_list)
#                 except Exception as sql_err:
#                     logger.error(f"寫入 drill_info 錯誤: {sql_err}")

#             if prediction_list:
#                 try:
#                     await prediction_crud.create_prediction_record_all(mydb, prediction_list)
#                 except Exception as sql_err:
#                     logger.error(f"寫入 prediction_record 錯誤: {sql_err}")

#             if highlight_list:
#                 try:
#                     mail_list = await mail_crud.get_mail_info(mydb)
#                     email_client.add_client(host=email_host)
#                     for highlight_info in highlight_list:
#                         send_data = transfer.get_mail_data(highlight_info, mail_list)
#                         logger.info(f"send mail: {send_data}")
#                         # email_client.send_email(host=email_host, data=send_data)
#                     logger.info("PPM highlight info 已寄出")
#                 except Exception as mail_err:
#                     logger.error(f"Mail send error: {mail_err}")
#                 finally:
#                     email_client.delete_client(host=email_host)

#             start_time = boards_info[-1].AOITime
#             logger.info(f"new start_time: {start_time}")

#         logger.info("No data need to update!")
#     logger.info(f"-----------------Mission Completed at {datetime.datetime.now()}------------------")
