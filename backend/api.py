from fastapi import FastAPI
from pydantic import BaseModel

from backend.query_engine import process_question

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AskDB API",
    description="Natural Language to SQL API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    conversation_context: str = ""


def _is_llm_unavailable_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    markers = [
        "gemini unavailable",
        "quota exhausted",
        "resource_exhausted",
        "429",
        "rate limit",
        "temporarily unavailable",
        "unavailable",
        "503",
    ]
    return any(marker in error_text for marker in markers)


def _build_error_payload(exc: Exception):
    if _is_llm_unavailable_error(exc):
        return {
            "success": False,
            "error_type": "llm_unavailable",
            "message": "AI service is temporarily unavailable.",
        }

    return {
        "success": False,
        "error_type": "internal_error",
        "message": "Something went wrong while processing your question.",
    }


@app.get("/")
def root():
    return {
        "message": "AskDB API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        response = process_question(
            question=request.question,
            conversation_context=request.conversation_context,
        )

        df = response["result"]

        return {
            "success": True,
            "question": response["question"],
            "answer": response["answer"],
            "sql": response["sql"],
            "result": df.to_dict(orient="records"),
            "repair_attempts": response["repair_attempts"],
        }

    except Exception as e:
        return _build_error_payload(e)
