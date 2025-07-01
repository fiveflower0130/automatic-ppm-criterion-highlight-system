import httpx
from app.config import Config

async def get_ai_classification(img_src: str, product_name: str, auth=None) -> dict:
    """
    呼叫 AI Service Center 進行機鑽圖分類預測
    :param img_src: 圖片路徑
    :param product_name: 產品名稱
    :param auth: 認證資訊，預設為 None
    :return: dict，包含分類結果或錯誤資訊
    """
    url = f"http://{Config.AI_SERVICE_HOST}:{Config.AI_SERVICE_PORT}/drill_map/classify"
    payload = {
        "img_src": img_src,
        "product_name": product_name
    }
    async with httpx.AsyncClient(
        proxies={'http://': None, 'https://': None},
        verify=False,
        trust_env=False,
        auth=auth,
        timeout=30
    ) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            resp_json = response.json()
            if resp_json.get("code") == "0":
                return resp_json["data"]
            else:
                # 回傳錯誤資訊
                return {
                    "classification_code": None,
                    "classification_model": None,
                    "distance": None,
                    "error": resp_json.get("error", "未知錯誤")
                }
        except Exception as e:
            return {
                "classification_code": None,
                "classification_model": None,
                "distance": None,
                "error": str(e)
            }
        
# start_time = datetime.datetime.now()
# test_img_path = 'C:\\Users\\k09857\\Desktop\\AI Services Center\\ai_service_center\\app\\ai_modules\\drill_map_ai\\data_model\\inference\\20241106132700ND11SP2L241025063Target.jpg'
# product_name = '1166 111 A002G REV.A'
# ai_classification_result = asyncio.run(get_ai_classification(test_img_path, product_name))
# end_time = datetime.datetime.now()
# print(ai_classification_result)
# print(f"total time: {(end_time - start_time)}")
