import os
import re
import math
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from app.utils.logger import Logger
from app.config import Config
from app.services.soap_service import SOAPService

class Singleton:
    """單例模式基類"""
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]

class DataTransfer(Singleton):

    def __init__(self):
        self.__execution_path = os.getcwd()
        self.__logger = Logger().get_logger()
        self.__soap_service = SOAPService()

    def __read_excel(self, file_path: str, sheet_name: str, usecols: list) -> pd.DataFrame:
        """讀取 Excel 文件"""
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, usecols=usecols)
        except Exception as err:
            self.__logger.error(f"讀取 Excel 文件失敗: {err}")
            raise

    async def get_ppm_criteria_limit_info(self, product_name: str, ar_value: float, ar_info: object)-> dict:
        """獲取PPM標準限制信息"""
        try:
            criteria_info = {
                "product_name": product_name,
                "ar": ar_value,
                "ar_level": 'N',
                "ppm_limit": -1,
                "modification": False,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            ar_value = float(ar_value)
            if ar_value > 0 and ar_info:
                for info in ar_info:
                    # 確保 info 物件具有所需的屬性
                    if hasattr(info, "upper_limit") and hasattr(info, "ar_level") and hasattr(info, "ppm_limit"):
                        if ar_value < info.upper_limit:
                            criteria_info["ar_level"] = info.ar_level
                            criteria_info["ppm_limit"] = info.ppm_limit
                            criteria_info["modification"] = info.ar_level == 'S'
                            break

            return criteria_info

        except Exception as err:
            self.__logger.error(f"get_ppm_criteria_limit_info fail: {err}")
            return {}
            

    async def get_ppm_ar_value(self, lot_number:str)-> float:
        """獲取PPM的AR值"""
        try:
            soap_params = {
                "ScheduleId": lot_number,
                "StepId": "7276" if len(lot_number) > 10 else "9241",
                "SPECType": "1",
                "InComChColumnName": "內層Annual Ring" if len(lot_number) > 10 else "外層Annual Ring"
            }
            return await self.__soap_service.call_soap_method(soap_params)

        except Exception as err:
            self.__logger.error(f"get_ppm_ar_value fail: {err}")
            return 0


    def get_all_ppm_criteria_limit(self)-> list:
        """獲取所有PPM標準限制"""
        file_name= self.__ppm_config.get("Excel", "ppm_file_name")
        file_name = Config.PPM_FILE_NAME
        file_path = os.path.join(self.__execution_path, file_name)
        # file_path = os.path.join(self.__execution_path, self.__config.get('Excel', 'ppm_file_name'))
        try:
            # sheet_name: 0->sheet1 , usecols: 0->圖號 5->AR 8->AR等級 12->散孔管制界限
            df = self.__read_excel(file_path, sheet_name='風險圖號', usecols=[0, 5, 8, 12])
                          
            # for i in range(len(df)):
            #     criteria_limit_dict = {}
            #     criteria_limit_dict['product_name'] = df.at[i, df.columns[0]] if df.at[i, df.columns[0]] else None
            #     criteria_limit_dict['ar'] = df.at[i, df.columns[1]] if df.at[i, df.columns[1]] else -1
            #     criteria_limit_dict['ar_level'] = df.at[i, df.columns[2]] if df.at[i, df.columns[2]] else None
            #     criteria_limit_dict['ppm_limit'] = int(df.at[i, df.columns[3]]) if df.at[i, df.columns[3]] else 0
            #     criteria_limit_dict['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #     criteria_limit_dict['modification'] = True if df.at[i, df.columns[2]] == 'S' else False
            #     rows.append(criteria_limit_dict)
            return [
                {
                    "product_name": row[0] or None,
                    "ar": row[1] or -1,
                    "ar_level": row[2] or None,
                    "ppm_limit": int(row[3]) if row[3] else 0,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "modification": row[2] == 'S'
                }
                for row in df.itertuples(index=False)
            ]
        except Exception as err:
            self.__logger.error(f"get_all_ppm_criteria_limit fail: {err}")
            return []
        # except Exception as err:
        #     self.__logger.error(f"get_all_ppm_criteria_limit fail: {err}")
        #     if self.__retry < 3:
        #         self.__retry = self.__retry + 1
        #         self.get_all_ppm_criteria_limit() 
        # finally:
        #     self.__retry = 0
        #     return rows
    
    def get_ppm_control_limit(self, product_name:str)-> int:
        """獲取PPM控制限制"""
        
        file_name= Config.PPM_FILE_NAME
        file_path = os.path.join(self.__execution_path, file_name)
        
        try:
            df = self.__read_excel(file_path, sheet_name='風險圖號', usecols=[0, 12])
            for row in df.itertuples(index=False):
                if row[0] == product_name:
                    return int(row[1])
            return -1
        except Exception as err:
            self.__logger.error(f"get_ppm_control_limit fail: {err}")
            return -1
        # try:
        #     # sheet_name: 0->sheet1 , usecols: 0->圖號 12->散孔管制界限
        #     df = pd.read_excel(file_path, sheet_name='風險圖號', usecols=[0, 12])
        #     for i in range(len(df)):
        #         ppm_criteria_limit_name = df.at[i, df.columns[0]] 
        #         if (ppm_criteria_limit_name == product_name):
        #             ppm_control_limit = int(df.at[i, df.columns[1]])
        # except Exception as err:
        #     self.__logger.error(f"get_ppm_control_limit fail: {err}")
        #     if self.__retry < 3:
        #         self.__retry = self.__retry + 1
        #         self.get_ppm_control_limit(product_name)
        #     else:     
        #         ppm_control_limit = -1
        # finally:
        #     self.__retry = 0
        #     return ppm_control_limit

    def __parse_date(self, date_str: str, formats: list) -> datetime:
        """解析日期字串"""
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"無法解析日期: {date_str}")
    
    def get_drill_info_transfer(self, board: object, measure: object, product: object, machine: object) -> dict:
        """轉換鑽孔資訊"""
        try:
            formats = ["%Y/%m/%d %H:%M:%S", "%Y/%m/%d"]
            drill_info = {
                "lot_number": str(board.Lot) if board.Lot else None,
                "product_name": str(product.product_name) if product.product_name else None,
                "drill_machine_name": str(machine.Name_DM) if machine.Name_DM else None,
                "drill_time": self.__parse_date(board.DrillTime, formats) if board.DrillTime else None,
                "aoi_time": self.__parse_date(board.AOITime, formats) if board.AOITime else None,
                "drill_machine_id": int(board.DrillMachineID),
                "drill_spindle_id": int(board.DrillSpindleID),
                "ppm_control_limit": int(product.ppm_limit) if product.ppm_limit else -1,
                "ratio_target": float(measure.RatioInTarget_Before) if measure else 0,
                "cpk": float(measure.Cpk_Z_Before) if measure else -1,
                "cp": float(measure.CP_Z_Before) if measure else -1,
                "ca": float(measure.CA_Z_Before) if measure else -1,
            }
            drill_info["ppm"] = (100 - drill_info["ratio_target"]) * 10000
            drill_info["judge_ppm"] = math.ceil(drill_info["ppm"]) <= drill_info["ppm_control_limit"]
            return drill_info
        except Exception as err:
            self.__logger.error(f"get_drill_info_transfer fail: {err}")
            return {}

    def __get_report_receivers(self, mail_list:list)->dict:
        """獲取報告接收者的電子郵件地址"""
        try:
            # data = {
            #     "to": ["Dante_Chen@aseglobal.com"],
            #     "cc": [],
            #     "bcc": []
            # }
            data = {
                "to": [],
                "cc": [],
                "bcc": [],
            }
            
            for mail in mail_list:
                # transfer object to dict
                if mail.send_type == "to":
                    data["to"].append(mail.email)
                if mail.send_type == "cc":
                    data["cc"].append(mail.email)
                if mail.send_type == "bcc":
                    data["bcc"].append(mail.email)
        
            return data
        
        except Exception as err:
            self.__logger.error(f"__get_report_receivers fail: {err}")
            return {"to": [], "cc": [], "bcc": []}
    
    def get_mail_data(self, highlight_info:dict, mail_list:list):
        """獲取郵件數據"""
        try:
            sender = {
                'name': 'Testing PPM Hightlight System Manager',
                'email': 'Testing_TID5940@aseglobal.com'
            }
            receivers = self.__get_report_receivers(mail_list)
            # receivers = {
            #     "to": ["Dante_Chen@aseglobal.com"],
            #     "cc": [],
            #     "bcc": []
            # }
            # print("receivers: ",receivers)
            
            # 獲取Webside的host和port
            webside_host = Config.WEBSIDE_HOST
            webside_port = Config.WEBSIDE_PORT

            # 建立郵件內容
            content =f"""
                <p>
                Dear all 這是Testing,<br> 
                機鑽穴位圖PPM已超出管制上限. 請EE立即至該機台確認<br>
                <br>
                1. 機台編號: {highlight_info['machine_name']}<br>
                2. 軸: {highlight_info['spindle_id']+1}<br>
                3. 批號: {highlight_info['lot_number']}<br>
                4. PPM: {math.floor(highlight_info['ppm'])}. (上限: {highlight_info['ppm_control_limit']})<br>
                <br>
                連結網頁: <a href="http://{webside_host}:{webside_port}/Result/PeViewPage?lot={highlight_info['lot_number']}">http://{webside_host}:{webside_port}/Result/PeViewPage?lot={highlight_info['lot_number']}</a>
                </p>
            """
            # 建立郵件主題
            subject = f"[Warning!!!!!][機鑽站] PPM out of control limit. 機台編號: {highlight_info['machine_name']}, 軸: {highlight_info['spindle_id']+1}, 批號: {highlight_info['lot_number']}"

            # 組織郵件數據
            send_data = {
                'from': sender,
                'to': receivers["to"],
                'cc': receivers["cc"],
                'bcc': receivers["bcc"],
                'subject': subject,
                'body': content,
                'attachment': []
            }
            return send_data
        except Exception as err:
            self.__logger.error(f"get_mail_data fail: {err}")
            return {'from': {},'to': [],'cc': [],'bcc': [],'subject': '','body': '','attachment': []}

    # 20240619 新增
    def __get_datetime_transfer_by_month(self, start_time:str, end_time:str)->dict:
        """根據開始時間和結束時間獲取每月的開始和結束日期"""
        try:
            result = {}
            start_date = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            current_date = start_date

            while current_date < end_date:
                next_month = current_date.replace(day=1) + timedelta(days=32)
                result[current_date.strftime("%Y-%m")] = [
                    current_date.replace(day=1).strftime('%Y-%m-%d %H:%M:%S'), 
                    next_month.replace(day=1).strftime('%Y-%m-%d %H:%M:%S')
                ]
                current_date = next_month.replace(day=1)
            return result
        except Exception as err:
            self.__logger.error(f"__get_datetime_transfer_by_month fail: {err}")
            return {}
    

    def __get_datetime_transfer_by_week(self, start_time:str, end_time:str):
        """根據開始時間和結束時間獲取每周的開始和結束日期"""
        result = {}
        try:
            start_date = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            current_date = start_date

            while current_date < end_date:
                # 調整開始日期為周日
                week_start = current_date - timedelta(days=(current_date.weekday() + 1) % 7)
                week_end = week_start + timedelta(days=7)

                # 計算 ISO 標準的週數
                week_number = (week_start + timedelta(days=1)).isocalendar()[1]
                year = week_start.year

                # 儲存結果，鍵為 "年份-週數"
                result[f"{year}-{week_number}"] = [
                    week_start.strftime('%Y-%m-%d %H:%M:%S'),
                    week_end.strftime('%Y-%m-%d %H:%M:%S')
                ]

                # 移動到下一週
                current_date = week_end
            
            # week_ranges = []
            # while current_date < end_date:
            #     # 調整開始日期改為周日為開始日期
            #     week_start = current_date - timedelta(days=(current_date.weekday() + 1) % 7)
            #     week_end = week_start + timedelta(days=7)
                
            #     week_ranges.append((week_start, week_end))
            #     current_date = week_start + timedelta(days=7)

            # # 顯示每周的開始日期和結束日期(計算週數調整為產線計算方式)
            # for i, (week_start, week_end) in enumerate(week_ranges, start=1):
            #     result[current_date.strftime("%Y")+"-"+str((week_start + timedelta(days=1)).isocalendar()[1])] = [week_start.strftime('%Y-%m-%d %H:%M:%S'),week_end.strftime('%Y-%m-%d %H:%M:%S')]
            #     # 取得開始日期所在的ISO周數isocalendar()
           
            return result
        except Exception as e:
            self.__logger.error(f"__get_datetime_transfer_by_week fail: {e}")
            return {}

    def __get_datetime_transfer_by_day(self, start_time:str, end_time:str):
        """根據開始時間和結束時間獲取每天的開始和結束日期"""
        try:
            result = {}
            start_date = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

            current_date = start_date

            while current_date <= end_date:
                result[current_date.strftime("%Y-%m-%d")] = [
                    current_date.strftime('%Y-%m-%d %H:%M:%S'), 
                    (current_date + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                ]
                current_date += timedelta(days=1)
            return result
        except Exception as e:
            self.__logger.error(f"__get_datetime_transfer_by_day fail: {e}")
            return {}    
    
    def get_datetime_transfer(self, start_time:str, end_time:str, transfer_type:str)->dict:
        """根據開始時間、結束時間和轉換類型獲取時間轉換字典"""
        if start_time > end_time:
            return {}

        transfer_methods = {
            "month": self.__get_datetime_transfer_by_month,
            "week": self.__get_datetime_transfer_by_week,
            "day": self.__get_datetime_transfer_by_day
        }

        transfer_method = transfer_methods.get(transfer_type)
        if transfer_method:
            return transfer_method(start_time, end_time)
        else:
            return {}
        
    def validate_datetime_format(self, datetime_str: str) -> bool:
        """驗證日期時間字串格式是否為 'YYYY-MM-DD HH:MM:SS'"""
        try:
            datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError: 
            return False
    
    def __get_data_transfer_by_freq(self, data:list, datetime_limit:dict)->dict:
        grouped_data = defaultdict(list)
        try:
            for item in data:
                for key, value in datetime_limit.items():
                    # 檢查 item.aoi_time 是否在指定的時間範圍內
                    start_time = datetime.strptime(value[0], "%Y-%m-%d %H:%M:%S")
                    end_time = datetime.strptime(value[1], "%Y-%m-%d %H:%M:%S")
                    if start_time <= item.aoi_time < end_time:
                        grouped_data[key].append(item)
        except Exception as err:
            self.__logger.error(f"__get_data_transfer_by_freq fail: {err}")
        return grouped_data
    
    def __get_failrate_count(self, data:dict)->dict:
        """計算失敗率"""  
        result = {}
        try:
            for key, value in data.items():
                total_count = len(value)
                fail_count = len([item for item in value if item.judge_ppm == 0])
                fail_rate = round(fail_count / total_count, 4) if total_count > 0 else 0
                result[key] = {
                    "total_count": total_count,
                    "fail_count": fail_count,
                    "fail_rate": fail_rate
                }
        except Exception as err:
            self.__logger.error(f"__get_failrate_count fail: {err}")
        return result
        
    def get_failrate_filter_data(self, data:list, datetime_limit:dict, drill_machine_name:str=None)->dict:
        """獲取失敗率過濾數據"""
        result = {}
        try:
            if drill_machine_name:
                freq_group = self.__get_data_transfer_by_freq(data, datetime_limit)
                result = self.__get_failrate_count(freq_group)
            else:
                # 分類 Hitachi 和 Posalux 機台資料
                hitachi_total = [item for item in data if item.drill_machine_name < "ND41"]
                posalux_total = [item for item in data if item.drill_machine_name > "ND40"]

                # 按時間範圍分組並計算失敗率
                hitachi_freq_group = self.__get_data_transfer_by_freq(hitachi_total, datetime_limit)
                posalux_freq_group = self.__get_data_transfer_by_freq(posalux_total, datetime_limit)

                result["hitachi"] = self.__get_failrate_count(hitachi_freq_group)
                result["posalux"] = self.__get_failrate_count(posalux_freq_group)

        except Exception as err:
            self.__logger.error(f"get_failrate_filter_data fail: {err}")
        return result
    

    # 20241105 新增
    async def get_ai_drill_img_path(self, lot_number:str, drill_machine_name:str, drill_spindle_id:int, drill_time:str)->str:
        """獲取AI鑽孔圖像路徑"""
        try:
            drill_img_folder = Config.DRILL_IMG_FOLDER
            if not isinstance(drill_spindle_id, int):
                drill_spindle_id = int(drill_spindle_id)

            # 格式化時間並生成檔案名稱
            drill_time_replace = re.sub(r'[-: T]', '', drill_time)
            img_file_name = f'{drill_time_replace}{drill_machine_name}SP{str(drill_spindle_id+1)}{lot_number}Target.jpg'
            
            # 組合路徑
            result = os.path.join(drill_img_folder, drill_machine_name, img_file_name)
            return result
        
        except Exception as err:
            self.__logger.error(f"get_drill_img_path [{lot_number}, {drill_machine_name}, {drill_spindle_id}, {drill_time}] fail: {err}")
            return None