from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
from config import STUDENT_ID

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # на етапі практики можна відкрити всім
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пам'ять для статей: { student_id: [ {title, link, published}, ... ] }
news_store = {STUDENT_ID: []}

# Initialize the analyzer
analyzer = SentimentIntensityAnalyzer()

@app.post("/fetch/{student_id}")
def fetch_news(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(404, "Student not found")
    fetched = 0
    news_store[student_id].clear()
    for url in config.SOURCES:
        feed = feedparser.parse(url)
        for entry in getattr(feed, "entries", []):
            # беремо основні поля
            news_store[student_id].append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", "")
            })
            fetched += 1
    return {"fetched": fetched}

@app.get("/news/{student_id}")
def get_news(student_id: str):
    if student_id not in news_store:
        raise HTTPException(404, "Student not found")
    return {"articles": news_store[student_id]}

@app.get("/info")
def info():
    return {"student_id": STUDENT_ID}

@app.post("/analyze/{student_id}")
def analyze_tone(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(404, "Student not found")
    articles = news_store.get(student_id, [])
    result = []
    for art in articles:
        text = art["title"] or ""
        scores = analyzer.polarity_scores(text)
        # Визначимо label за compound
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
