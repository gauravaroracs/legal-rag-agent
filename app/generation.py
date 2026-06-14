from openai import OpenAI

from app.config import get_settings
from app.retrieval import retrieve_chunks
from app.schemas import RetrievedChunk


def format_context(chunks: list[RetrievedChunk]) -> str:
    formatted_chunks = []

    for idx, chunk in enumerate(chunks, start=1):
        formatted_chunks.append(
            f"""
[Citation {idx}]
Source: {chunk.source}
Page: {chunk.page}
Chunk: {chunk.chunk_index}

Text:
{chunk.text}
""".strip()
        )

    return "\n\n---\n\n".join(formatted_chunks)

def is_retrieval_relevant(chunks: list[RetrievedChunk], max_distance: float = 0.60) -> bool:

    if not chunks:

        return False

    best_score = chunks[0].score

    if best_score is None:

        return False

    return best_score <= max_distance

def answer_question(question: str, top_k: int = 5) -> dict:

    settings = get_settings()

    client = OpenAI(api_key=settings.openai_api_key)

    chunks = retrieve_chunks(question, top_k=top_k)

    if not is_retrieval_relevant(chunks):

        return {

            "answer": (

                "The indexed document does not contain sufficiently relevant information "

                "to answer this question with reliable citations."

            ),

            "citations": [],

        }

    context = format_context(chunks)

    system_prompt = """

You are a careful legal AI assistant.

Answer ONLY using the provided context.

Do not use outside knowledge.

If the context does not contain enough information, say that the provided document excerpts are insufficient.

Every factual claim must be supported by citations.

Use citation format like: [legal.pdf, p. 37].

Be precise, cautious, and avoid overclaiming.

""".strip()

    user_prompt = f"""

Question:

{question}

Context:

{context}

""".strip()

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {"role": "system", "content": system_prompt},

            {"role": "user", "content": user_prompt},

        ],

        temperature=0.1,

    )

    answer = response.choices[0].message.content

    return {

        "answer": answer,

        "citations": [chunk.model_dump() for chunk in chunks],

    }
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    chunks = retrieve_chunks(question, top_k=top_k)
    context = format_context(chunks)

    system_prompt = """
You are a careful legal AI assistant.

Answer ONLY using the provided context.
Do not use outside knowledge.
If the context does not contain enough information, say that the provided document excerpts are insufficient.
Every factual claim must be supported by citations.
Use citation format like: [legal.pdf, p. 37].
Be precise, cautious, and avoid overclaiming.
""".strip()

    user_prompt = f"""
Question:
{question}

Context:
{context}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "citations": [chunk.model_dump() for chunk in chunks],
    }


if __name__ == "__main__":
    result = answer_question("What does this document say about Indian tax law?")

    print("\nANSWER:")
    print(result["answer"])

    print("\nRETRIEVED CITATIONS:")
    for citation in result["citations"]:
        print(
            f"- {citation['source']}, page {citation['page']}, "
            f"chunk {citation['chunk_index']}, score {citation['score']}"
        )