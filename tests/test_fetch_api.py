import pytest
import importlib.util
from fastapi.testclient import TestClient
from backend.app import app, news_store, sources_store
from config import STUDENT_ID
import feedparser

client = TestClient(app)

def test_get_news_empty(monkeypatch):
    # Гарантуємо, що х store порожній
    news_store[STUDENT_ID] = []
    res = client.get(f"/news/{STUDENT_ID}")
    assert res.status_code == 200
    assert res.json() == {"articles": []}

class DummyFeed:
    entries = [
        {"title":"T1","link":"http://a","published":"2025-01-01"},
        {"title":"T2","link":"http://b","published":""}
    ]

def test_fetch_and_get(monkeypatch):
    # Видаляємо маніпуляції з config.SOURCES
    # monkeypatch.setenv("SOURCES", "")
    # monkeypatch.setattr("config.SOURCES", ["http://example.com/rss"])

    # Підмінюємо парсер
    monkeypatch.setattr(feedparser, "parse", lambda url: DummyFeed)

    # Очищуємо сховища перед тестом (добра практика)
    news_store.pop(STUDENT_ID, None)
    sources_store.pop(STUDENT_ID, None)

    # Додаємо тестове джерело через API
    add_source_res = client.post(f"/sources/{STUDENT_ID}", json={"url": "http://example.com/test_rss"})
    assert add_source_res.status_code == 200
    assert "http://example.com/test_rss" in add_source_res.json()["sources"]

    # Запускаємо fetch
    res1 = client.post(f"/fetch/{STUDENT_ID}")
    assert res1.status_code == 200
    # Перевіряємо, що завантажено 2 новини з одного джерела
    assert res1.json() == {"fetched": 2} # DummyFeed має 2 записи

    # Перевіряємо GET
    res2 = client.get(f"/news/{STUDENT_ID}")
    assert res2.status_code == 200
    # Оновлена перевірка відповіді відповідно до DummyFeed
    data = res2.json()
    assert "articles" in data
    assert len(data["articles"]) == 2
    assert data["articles"][0]["title"] == "T1"
    assert data["articles"][0]["link"] == "http://a"
    assert data["articles"][0]["published"] == "2025-01-01"
    assert data["articles"][1]["title"] == "T2"
    assert data["articles"][1]["link"] == "http://b"
    assert data["articles"][1]["published"] == ""
