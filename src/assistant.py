import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from .ingest import get_store
from .guardrails import redact_pii

class KBAnswer(BaseModel):
    """Structured output — LangChain validates this automatically."""
    answer: str = Field(description="Reply shown to the employee")
    citations: list[str] = Field(default_factory=list, description="doc_ids used")
    abstained: bool = Field(default=False, description="True if KB doesn't support")

SYSTEM = """You are Vectra Logistics' IT helpdesk assistant.
Answer ONLY from the provided KB excerpts. Rules:
1. If excerpts don't cover the question, set abstained=true, citations=[], and say "Please raise a ticket with the IT service desk."
2. Never invent URLs, error codes, phone numbers, or processes.
3. Cite the doc_id(s) you actually used.
4. For P1 incidents, include KB-003's phone instruction (ext. 4357).
Return strict structured output.
"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("user", "KB excerpts:\n{context}\n\nEmployee question:\n{question}"),
])

def _format_context(docs) -> str:
    return "\n\n".join(f"[{d.metadata['doc_id']} | {d.metadata['title']}]\n{d.page_content}" for d in docs)

def build_chain():
    store = get_store()
    retriever = store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 4, "score_threshold": 0.35},
    )
    llm = ChatOpenAI(model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-5.4-mini"), temperature=0)
    structured_llm = llm.with_structured_output(KBAnswer)

    def retrieve_and_answer(inputs: dict) -> KBAnswer:
        docs = retriever.invoke(inputs["question"])
        if not docs:
            return KBAnswer(
                answer="I don't have a KB article that covers this. Please raise a ticket with the IT service desk.",
                citations=[], abstained=True,
            )
        chain = PROMPT | structured_llm
        result: KBAnswer = chain.invoke({
            "context": _format_context(docs),
            "question": inputs["question"],
        })
        # Defensive: strip citations not in retrieved set
        allowed = {d.metadata["doc_id"] for d in docs}
        result.citations = [c for c in result.citations if c in allowed]
        if not result.citations and not result.abstained:
            return KBAnswer(answer="Please raise a ticket with the IT service desk.",
                            citations=[], abstained=True)
        return result

    return RunnableLambda(retrieve_and_answer)


def answer(question: str) -> dict:
    safe_question = redact_pii(question)          # <-- guardrails.py used HERE
    result = build_chain().invoke({"question": safe_question})
    return result.model_dump()
