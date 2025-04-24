# backend/Dockerfile

# 1. Базовый образ с Python
FROM python:3.13-slim

# 2. Создать рабочую директорию
WORKDIR /app

# 3. Скопировать файлы кода и requirements
COPY ./backend /app
COPY config.py /app

# 4. Установить зависимости
RUN pip install --no-cache-dir fastapi uvicorn feedparser vaderSentiment

# 5. Открыть порт
EXPOSE 8000

# 6. Запуск сервера
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
