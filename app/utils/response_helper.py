def resp(errMsg, data=None):
    result = {"code": "0", "error": ""}
    if errMsg is not None:
        result["code"] = "1"
        result["error"] = errMsg
    else:
        result["data"] = data
    return result