from fastapi import FastAPI
from app.routes import drill_router, feedback_router, mail_router, ppm_router, user_router

app = FastAPI()

# 註冊路由
app.include_router(drill_router)
app.include_router(feedback_router)
app.include_router(user_router)
app.include_router(mail_router)
app.include_router(ppm_router)

@app.get("/", summary="Root Endpoint", description="Welcome message for the AUTO PPM API")
async def root():
    return {"message": "Welcome to the AUTO PPM API!"}
