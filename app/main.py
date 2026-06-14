from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.agent import answer_question_with_agent
from app.schemas import QueryRequest, QueryResponse

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "legal.pdf"

app = FastAPI(
    title="Legal Case RAG Agent",
    description="A citation-grounded legal RAG prototype for arbitration documents.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/document", include_in_schema=False)
def document() -> FileResponse:
    return FileResponse(PDF_PATH, media_type="application/pdf", filename="legal.pdf")


@app.post("/query", response_model=QueryResponse)
def query_legal_document(request: QueryRequest) -> QueryResponse:
    result = answer_question_with_agent(request.question)

    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        rewritten_question=result["rewritten_question"],
        attempts=result["attempts"],
        evidence_supported=result["evidence_supported"],
        flow=result["flow"],
    )
