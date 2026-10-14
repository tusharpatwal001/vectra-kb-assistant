import re, yaml, pathlib
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

class KBArticleLoader(BaseLoader):
    """Loads .md KB articles, preserving YAML front-matter as metadata."""

    def __init__(self, folder: str = "kb_articles"):
        self.folder = pathlib.Path(folder)

    def load(self) -> list[Document]:
        docs = []
        for path in sorted(self.folder.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            m = FRONT_MATTER_RE.match(raw)
            if not m:
                continue
            meta = yaml.safe_load(m.group(1))
            body = m.group(2).strip()

            # Split on ## headings — keeps tables intact
            chunks = [c.strip() for c in re.split(r"\n(?=## )", body) if c.strip()]

            for i, chunk in enumerate(chunks):
                docs.append(Document(
                    page_content=chunk,
                    metadata={
                        "doc_id": meta["doc_id"],
                        "title": meta.get("title", ""),
                        "status": meta.get("status", "current"),
                        "effective_date": str(meta.get("effective_date", "")),
                        "superseded_by": meta.get("superseded_by", ""),
                        "chunk_index": i,
                    },
                ))
        return docs