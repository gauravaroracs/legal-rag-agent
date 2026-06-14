from pathlib import Path
from pypdf import PdfReader

from app.schemas import DocumentChunk


def read_pdf_pages(pdf_path: str) -> list[dict]:
    reader = PdfReader(pdf_path)
    pages: list[dict] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            pages.append(
                {
                    "source": Path(pdf_path).name,
                    "page": page_number,
                    "text": text.strip(),
                }
            )

    return pages


def chunk_text(text: str, chunk_size: int = 450, overlap: int = 80) -> list[str]:
    words = text.split()

    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

        if start < 0:
            start = 0

        if start >= len(words):
            break

    return chunks


def load_pdf_as_chunks(pdf_path: str) -> list[DocumentChunk]:
    pages = read_pdf_pages(pdf_path)
    all_chunks: list[DocumentChunk] = []

    for page in pages:
        chunks = chunk_text(page["text"])

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{page['source']}-p{page['page']}-c{idx}"

            all_chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=chunk,
                    source=page["source"],
                    page=page["page"],
                    chunk_index=idx,
                )
            )

    return all_chunks


if __name__ == "__main__":
    chunks = load_pdf_as_chunks("data/legal.pdf")

    print(f"Loaded {len(chunks)} chunks")
    print(chunks[0].model_dump())