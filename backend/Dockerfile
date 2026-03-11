FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖和证书
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# pip 升级并安装依赖
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
       -i https://pypi.org/simple

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]