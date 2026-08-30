# Базовый образ Python
FROM python:3.12-slim

# Не пишем .pyc и не буферизуем stdout/stderr — удобнее логи в контейнере
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала зависимости — слой кешируется, пока requirements.txt не менялся
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем исходный код
COPY . .

# Порт приложения внутри docker-сети (наружу не пробрасывается)
EXPOSE 8000

CMD ["python", "main.py"]
