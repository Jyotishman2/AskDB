from fastapi.testclient import TestClient

from backend.api import app


client = TestClient(app)


def test_ask_returns_structured_llm_unavailable_error(monkeypatch):
    def fake_process_question(*args, **kwargs):
        raise RuntimeError("Gemini unavailable / quota exhausted")

    monkeypatch.setattr("backend.api.process_question", fake_process_question)

    response = client.post(
        "/ask",
        json={"question": "How many customers are there?", "conversation_context": ""},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "error_type": "llm_unavailable",
        "message": "AI service is temporarily unavailable.",
    }
