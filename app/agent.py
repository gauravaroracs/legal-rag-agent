from typing import TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI

from app.config import get_settings
from app.generation import format_context, is_retrieval_relevant
from app.retrieval import retrieve_chunks
from app.schemas import RetrievedChunk


class AgentState(TypedDict):
    question: str
    rewritten_question: str | None
    chunks: list[RetrievedChunk]
    evidence_supported: bool
    answer: str
    attempts: int
    flow: list[str]


def retrieve_node(state: AgentState) -> AgentState:
    query = state["rewritten_question"] or state["question"]
    chunks = retrieve_chunks(query, top_k=5)

    return {
        **state,
        "chunks": chunks,
        "attempts": state["attempts"] + 1,
        "flow": [*state["flow"], "retrieve"],
    }


def rewrite_query_node(state: AgentState) -> AgentState:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    prompt = f"""
Rewrite the user's legal research question into a better search query for arbitration rules.

Original question:
{state["question"]}

Rules:
- Keep it short.
- Use legal/arbitration terminology.
- Do not answer the question.
- Only output the rewritten search query.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    rewritten = response.choices[0].message.content.strip()

    return {
        **state,
        "rewritten_question": rewritten,
        "flow": [*state["flow"], "rewrite_query"],
    }


def grade_evidence_node(state: AgentState) -> AgentState:
    if not is_retrieval_relevant(state["chunks"]):
        return {
            **state,
            "evidence_supported": False,
            "flow": [*state["flow"], "grade_evidence"],
        }

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    context = format_context(state["chunks"])

    prompt = f"""
You are grading whether retrieved legal excerpts can support an answer.

Question:
{state["question"]}

Retrieved excerpts:
{context}

Rules:
- Return SUPPORTED only if the excerpts directly answer the question.
- Return UNSUPPORTED if the answer would require outside knowledge.
- Return UNSUPPORTED if the question asks about a legal domain, jurisdiction, statute, or topic not directly present in the excerpts.
- Output exactly one word: SUPPORTED or UNSUPPORTED.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    grade = (response.choices[0].message.content or "").strip().upper()

    return {
        **state,
        "evidence_supported": grade == "SUPPORTED",
        "flow": [*state["flow"], "grade_evidence"],
    }


def generate_answer_node(state: AgentState) -> AgentState:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    context = format_context(state["chunks"])

    system_prompt = """
You are a careful legal AI assistant.

Answer ONLY using the provided context.
Do not use outside knowledge.
Every factual claim must be supported by citations.
Use citation format like: [legal.pdf, p. 37].
If the provided context is insufficient, say so.
Be precise, cautious, and avoid overclaiming.
""".strip()

    user_prompt = f"""
Question:
{state["question"]}

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

    return {
        **state,
        "answer": response.choices[0].message.content,
        "flow": [*state["flow"], "generate_answer"],
    }


def refuse_node(state: AgentState) -> AgentState:
    return {
        **state,
        "answer": (
            "The indexed document does not contain sufficiently relevant information "
            "to answer this question with reliable citations."
        ),
        "chunks": [],
        "flow": [*state["flow"], "refuse"],
    }


def decide_after_evidence_grade(state: AgentState) -> str:
    if state["evidence_supported"]:
        return "generate_answer"

    if state["attempts"] < 2:
        return "rewrite_query"

    return "refuse"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("grade_evidence", grade_evidence_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("refuse", refuse_node)

    graph.set_entry_point("retrieve")

    graph.add_edge("retrieve", "grade_evidence")

    graph.add_conditional_edges(
        "grade_evidence",
        decide_after_evidence_grade,
        {
            "generate_answer": "generate_answer",
            "rewrite_query": "rewrite_query",
            "refuse": "refuse",
        },
    )

    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate_answer", END)
    graph.add_edge("refuse", END)

    return graph.compile()


legal_rag_agent = build_graph()


def answer_question_with_agent(question: str) -> dict:
    initial_state: AgentState = {
        "question": question,
        "rewritten_question": None,
        "chunks": [],
        "evidence_supported": False,
        "answer": "",
        "attempts": 0,
        "flow": [],
    }

    result = legal_rag_agent.invoke(initial_state)

    return {
        "answer": result["answer"],
        "citations": [chunk.model_dump() for chunk in result["chunks"]],
        "rewritten_question": result["rewritten_question"],
        "attempts": result["attempts"],
        "evidence_supported": result["evidence_supported"],
        "flow": result["flow"],
    }


if __name__ == "__main__":
    questions = [
        "Can someone get urgent protection before the tribunal exists?",
        "What does the document say about Indian tax law?",
    ]

    for question in questions:
        print("=" * 100)
        print(f"QUESTION: {question}")

        result = answer_question_with_agent(question)

        print("\nREWRITTEN QUERY:")
        print(result["rewritten_question"])

        print("\nATTEMPTS:")
        print(result["attempts"])

        print("\nANSWER:")
        print(result["answer"])

        print("\nCITATIONS:")
        for citation in result["citations"]:
            print(
                f"- {citation['source']}, page {citation['page']}, "
                f"chunk {citation['chunk_index']}, score {citation['score']}"
            )
