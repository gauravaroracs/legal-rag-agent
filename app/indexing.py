import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import get_settings
from app.ingestion import load_pdf_as_chunks


def get_chroma_collection():
    settings = get_settings()

    client = chromadb.PersistentClient(path=settings.chroma_path)

    embedding_function = OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.embedding_model,
    )

    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def index_pdf(pdf_path: str) -> None:
    collection = get_chroma_collection()
    chunks = load_pdf_as_chunks(pdf_path)

    ids = [chunk.id for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [
        {
            "source": chunk.source,
            "page": chunk.page,
            "chunk_index": chunk.chunk_index,
        }
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"Indexed {len(chunks)} chunks into ChromaDB")


if __name__ == "__main__":
    index_pdf("data/legal.pdf")