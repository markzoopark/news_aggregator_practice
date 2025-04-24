# frontend/Dockerfile

# 1. Используем легкий HTTP-сервер (nginx)
FROM nginx:alpine

# 2. Копируем статику в папку /usr/share/nginx/html
COPY ./frontend /usr/share/nginx/html

# 3. Открыть порт
EXPOSE 80

# 4. (опционально) замените default nginx.conf, если нужно
