from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, items, categories, admin
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="校园二手物品平台 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(items.router, prefix="/api/items", tags=["物品"])
app.include_router(categories.router, prefix="/api/categories", tags=["类别"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理员"])


@app.get("/")
def root():
    return {"message": "校园二手物品平台 API 运行正常"}
