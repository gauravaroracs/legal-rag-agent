from fastapi import FastAPI

from app.agent import answer_question_with_agent
from app.schemas import QueryRequest, QueryResponse


app = FastAPI(
    title="Legal Case RAG Agent",
    description="A citation-grounded legal RAG prototype for arbitration documents.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_legal_document(request: QueryRequest) -> QueryResponse:
    result = answer_question_with_agent(request.question)

    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
    )
