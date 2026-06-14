from app.indexing import get_chroma_collection
from app.schemas import RetrievedChunk


def retrieve_chunks(question: str, top_k: int = 5) -> list[RetrievedChunk]:
    collection = get_chroma_collection()

    results = collection.query(
        query_texts=[question],
        n_results=top_k,
    )

    retrieved: list[RetrievedChunk] = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for document, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append(
            RetrievedChunk(
                text=document,
                source=metadata["source"],
                page=metadata["page"],
                chunk_index=metadata["chunk_index"],
                score=distance,
            )
        )

    return retrieved


if __name__ == "__main__":
    question = "What does the document say about emergency arbitration?"
    chunks = retrieve_chunks(question)

    for chunk in chunks:
        print("=" * 80)
        print(f"Source: {chunk.source}, page {chunk.page}, chunk {chunk.chunk_index}")
        print(f"Distance: {chunk.score}")
        print(chunk.text[:800])