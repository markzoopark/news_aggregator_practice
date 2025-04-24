from fastapi.testclient import TestClient
from backend.app import app, news_store
from config import STUDENT_ID
import vaderSentiment.vaderSentiment as vs

client = TestClient(app)

def test_analyze_empty():
    news_store[STUDENT_ID] = []
    res = client.post(f"/analyze/{STUDENT_ID}")
    assert res.status_code == 200
    assert res.json() == {"analyzed": 0, "articles": []}

class DummyArticle:
    def __init__(self, title, link, published):
        self.title = title
        self.link = link
        self.published = published

def test_analyze_real(monkeypatch):
    # Підготуємо дві статті
    news_store[STUDENT_ID] = [
        {"title":"I love this","link":"u1","published":""},
        {"title":"I hate that","link":"u2","published":""}
    ]

    # Підмінюємо sentiment-аналітик
    class FakeAnalyzer:
        def polarity_scores(self, txt):
            if "love" in txt:
                return {"neg":0.0,"neu":0.3,"pos":0.7,"compound":0.8}
            else:
                return {"neg":0.6,"neu":0.4,"pos":0.0,"compound":-0.6}

    monkeypatch.setattr(vs, "SentimentIntensityAnalyzer", FakeAnalyzer)

    res = client.post(f"/analyze/{STUDENT_ID}")
    data = res.json()
    assert res.status_code == 200
    assert data["analyzed"] == 2
    arts = data["articles"]
    assert arts[0]["sentiment"] == "positive"
    assert arts[1]["sentiment"] == "negative"
    # Перевіримо що scores передано
    assert "compound" in arts[0]["scores"]
