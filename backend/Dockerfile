# 使用官方 Python slim 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 禁止生成 pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt update && apt install -y --no-install-recommends \
    gcc g++ ca-certificates \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 复制本地下载好的依赖包
COPY packages /app/packages
COPY requirements.txt .

# 离线安装依赖
#RUN pip install --upgrade pip \
    #&& pip install --no-index --find-links=/app/packages -r requirements.txt

# 新命令：先尝试离线装，失败则去掉--no-index在线装
RUN pip install --upgrade pip \
    && (pip install --no-index --find-links=/app/packages -r requirements.txt || pip install -r requirements.txt)


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

# 启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# 新增：强制切换到 root 用户
USER root
# 保留权限配置
RUN mkdir -p /app && chmod 777 /app