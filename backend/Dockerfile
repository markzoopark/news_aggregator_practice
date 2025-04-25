FROM python:3.13-slim
WORKDIR /app

# Копіюємо та інсталюємо оновлені залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код і конфіг
COPY backend/   ./
COPY config.py  ./
COPY .env       ./

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
