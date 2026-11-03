from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_golden_cases_endpoint():
    response = client.get("/api/cases")
    assert response.status_code == 200
    assert len(response.json()) >= 5

def test_chat_endpoint(monkeypatch):
    # Keep automated tests deterministic and free of external API usage.
    from app.services.chatbot import DemoSmartHomeBot
    monkeypatch.setattr("app.main.chatbot", DemoSmartHomeBot())
    response = client.post("/api/chat", json={"message": "How do I reset my fan?"})
    assert response.status_code == 200
    assert "answer" in response.json()
