# 使用官方 Python slim 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 禁止生成 pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（包括 Tesseract OCR）
RUN apt update && apt install -y --no-install-recommends \
    gcc g++ ca-certificates \
    tesseract-ocr \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制后端源码
COPY . .

# 创建数据目录
RUN mkdir -p /app/vector_db /app/chroma_db /app/data \
    && chmod 755 /app/vector_db /app/chroma_db /app/data

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]