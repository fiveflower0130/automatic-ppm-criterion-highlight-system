import asyncio
import os
import datetime
from app.utils.data_transfer import DataTransfer
from app.crud import ppm as ppm_crud
from app.database import mssql_session, mysql_session


transfer = DataTransfer()

async def main():
    image_path = r"D:\drill_map_backup\ND51\20251003122700ND51SP2L250829120Target.jpg"
    # image_path = r"D:\drill_map_backup\ND07\20250922211100ND07SP5L250912062Target.jpg"
    create_time = transfer.get_image_update_time(image_path)
    print("create_time:", create_time)
    # if not create_time:
    #     file_mtime = os.path.getmtime(image_path)
    #     create_time = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")
    #     print("file_mtime:", create_time)

    # lot_number = "L250912062"
    # product_name = "A345370"
    # ppm_ar_value_info = transfer.get_ppm_ar_value(lot_number)
    # print("ppm_ar_value_info:", ppm_ar_value_info)
    # ppm_ar_value = ppm_ar_value_info.get("ColumnValue_1", 0)
    # print("ppm_ar_value:", ppm_ar_value)
    # async with mysql_session() as mydb:
    #     ppm_ar_limit_info = await ppm_crud.get_ppm_ar_limit_info(mydb)
    #     ppm_criteria_limit_info = await transfer.get_ppm_criteria_limit_info(
    #                     product_name=product_name, ar_value=ppm_ar_value, ar_info=ppm_ar_limit_info
    #                 )
    #     print("ppm_criteria_limit_info:", ppm_criteria_limit_info)

if __name__ == "__main__":
    asyncio.run(main())