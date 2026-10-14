import os
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from .loaders import KBArticleLoader
from dotenv import load_dotenv

load_dotenv()
CONNECTION = os.environ["PG_DSN"].replace("postgresql://", "postgresql+psycopg://")
COLLECTION = "vectra_kb"

def get_store() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
        collection_name=COLLECTION,
        connection=CONNECTION,
        use_jsonb=True,
    )

def ingest():
    docs = KBArticleLoader("kb_articles").load()
    print([d.metadata["doc_id"] for d in docs])

    # Skip deprecated / unverified at ingestion (documented choice)
    current = [d for d in docs if d.metadata["status"] == "current"]
    print(f"{current=}")
    skipped = [d for d in docs if d.metadata["status"] != "current"]
    print(f"{skipped=}")
    for d in skipped:
        print(f"SKIP {d.metadata['doc_id']} ({d.metadata['status']})")

    store = get_store()
    store.add_documents(documents=current)
    print(f"Ingested {len(current)} chunks from {len(set(d.metadata['doc_id'] for d in current))} articles")

if __name__ == "__main__":
    ingest()