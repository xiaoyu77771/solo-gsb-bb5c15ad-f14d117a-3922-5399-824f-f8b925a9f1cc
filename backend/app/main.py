import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, DATABASE_PATH, engine
from .routers import events, reveal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 随启动完成数据库初始化：建库目录 + 建表
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="秘密赠礼抽签", version="1.0.0", lifespan=lifespan)

app.include_router(events.router)
app.include_router(reveal.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 生产环境托管 React 构建产物（frontend/dist 由 Docker 多阶段构建拷入）
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str, request: Request):
        # /api 下未匹配的路由返回 JSON 404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="接口不存在")
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        # 其余路径交给前端路由处理
        return FileResponse(STATIC_DIR / "index.html")
