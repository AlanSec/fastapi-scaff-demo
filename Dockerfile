FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先装依赖（利用层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# factory 模式启动（与 main.py 一致）
CMD ["uvicorn", "src.bootstrap.lifespan:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
