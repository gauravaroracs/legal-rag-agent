from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    id: str
    text: str
    source: str
    page: int
    chunk_index: int


class RetrievedChunk(BaseModel):
    text: str
    source: str
    page: int
    chunk_index: int
    score: float | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)


class QueryResponse(BaseModel):
    answer: str
    citations: list[RetrievedChunk]