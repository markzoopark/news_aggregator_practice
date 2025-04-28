from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

import config
from config import STUDENT_ID

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List

app = FastAPI()

# Определяем список разрешенных origins
origins = [
    "http://localhost:8001",   # фронтенд у Docker
    "http://127.0.0.1:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Используем определенный список origins
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ------------------ 2. Конфіг для JWT ------------------
SECRET_KEY = getattr(config, 'SECRET_KEY', 'default_secret_key_please_change')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ------------------ 3. Псевдо-БД користувачів ------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fake_users_db = {
    "student1": {
        "username": "student1",
        "hashed_password": pwd_context.hash("password123"),
        "role": "student"
    },
    "teacher": {
        "username": "teacher",
        "hashed_password": pwd_context.hash("teachpass"),
        "role": "teacher"
    }
}

# Додамо вашого STUDENT_ID як користувача, якщо його ще немає
if config.STUDENT_ID not in fake_users_db:
     fake_users_db[config.STUDENT_ID] = {
         "username": config.STUDENT_ID,
         # Потрібно придумати безпечний пароль або механізм його генерації/встановлення
         "hashed_password": pwd_context.hash("password123"),
         "role": "student"
     }

# ------------------ 4. Схема OAuth2 ------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ------------------ 5. Утиліти для аутентифікації ------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db, username: str, password: str):
    user = db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    # Перевіряємо, чи співпадає username з STUDENT_ID для студента
    if user["role"] == "student" and username != config.STUDENT_ID:
         # Дозволяємо логін тільки для STUDENT_ID з роллю student
         # Або для teacher, якщо логіниться вчитель
         if username != "teacher": # Дозволяємо вчителю логінитися під своїм ім'ям
              return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ------------------ 6. Ендпоінт для логіну ------------------
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невірні облікові дані або ім'я користувача")
    access_token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------ 7. Декоратори для захисту маршрутів ------------------
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    if user["role"] != role:
        raise credentials_exception
    return {"username": username, "role": role}

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав")
        return current_user
    return role_checker

# Пам'ять для джерел RSS: { student_id: [url1, url2, ...] }
# Ініціалізуємо порожнім, щоб тести могли контролювати стан
sources_store: Dict[str, List[str]] = {}

# Пам'ять для статей: { student_id: [ {title, link, published}, ... ] }
news_store = {STUDENT_ID: []}

# Initialize the analyzer
analyzer = SentimentIntensityAnalyzer()

@app.get("/info")
def info():
    return {"student_id": STUDENT_ID}

@app.post("/fetch/{student_id}")
async def fetch_news(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student ID не знайдено")
    fetched = 0
    # Ініціалізуємо або очищуємо список новин для студента
    news_store.setdefault(student_id, []).clear()
    # Використовуємо список джерел зі сховища
    for url in sources_store.get(student_id, []):
        feed = feedparser.parse(url)
        for entry in getattr(feed, "entries", []):
            news_store[student_id].append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", "")
            })
            fetched += 1
    return {"fetched": fetched}

@app.get("/news/{student_id}")
def get_news(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student ID не знайдено")
    if student_id not in news_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новини для цього ID ще не завантажені")
    return {"articles": news_store[student_id]}

@app.post("/analyze/{student_id}")
async def analyze_tone(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student ID не знайдено")
    articles = news_store.get(student_id, [])
    result = []
    for art in articles:
        text = art["title"] or ""
        scores = analyzer.polarity_scores(text)
        comp = scores["compound"]
        if comp >= 0.05:
            label = "positive"
        elif comp <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        result.append({
            "title": art["title"],
            "link": art["link"],
            "published": art["published"],
            "sentiment": label,
            "scores": scores
        })
    return {"analyzed": len(result), "articles": result}

# --- Нові ендпоінти для керування джерелами --- 

@app.get("/sources/{student_id}")
def get_sources(student_id: str):
    # Перевірка чи студент існує (можна додати, якщо потрібно більш строгу логіку)
    # if student_id not in fake_users_db:
    #     raise HTTPException(status_code=404, detail="Student ID not found")
    # Повертаємо словник відповідно до очікувань тесту
    return {"sources": sources_store.get(student_id, [])}

@app.post("/sources/{student_id}")
def add_source(student_id: str, payload: dict):
    # Перевірка чи студент існує (можна додати)
    # if student_id not in fake_users_db:
    #     raise HTTPException(status_code=404, detail="Student ID not found")
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Параметр 'url' обов'язковий")
    # Додаємо джерело до списку студента, створюючи список якщо його немає
    sources_store.setdefault(student_id, []).append(url)
    # Повертаємо словник відповідно до очікувань тесту
    return {"sources": sources_store[student_id]}
