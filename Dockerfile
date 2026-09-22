# ---- 阶段 1：构建 React 静态资源 ----
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 阶段 2：FastAPI 运行环境 ----
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_PATH=/data/secret_santa.db \
    PORT=8000

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 后端代码
COPY backend/app ./app

# 前端构建产物（FastAPI 直接托管）
COPY --from=frontend-build /build/dist ./static

# SQLite 数据目录（挂载为持久卷）
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

# 数据库目录/表随启动自动创建（见 app/main.py 的 lifespan）
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
