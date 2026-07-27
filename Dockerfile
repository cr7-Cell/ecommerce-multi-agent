# ============================================================
# 跨境电商多智能体系统 - Docker 镜像
# ============================================================
# 多阶段构建：减小镜像体积，分离构建与运行环境
#
# 构建:
#   docker build -t ecommerce-multi-agent:latest .
#
# 运行:
#   docker run -p 7000:7000 --env-file .env ecommerce-multi-agent:latest
# ============================================================

# ---- Stage 1: 构建阶段 ----
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖（编译用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

# 安装 Python 依赖到临时目录
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: 运行阶段 ----
FROM python:3.11-slim

WORKDIR /app

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:7000/health').raise_for_status()" || exit 1

# 暴露端口
EXPOSE 7000

# 默认启动 API 服务
CMD ["python", "main.py", "--api"]