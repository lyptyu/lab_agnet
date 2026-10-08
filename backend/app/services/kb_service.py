from app.config import settings
from chromadb import Collection
from app.config import BASE_DIR
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

KB_DIR = BASE_DIR / "data" / "kb"

CHROMA_DIR = BASE_DIR / "data" / "chroma"
_collection = None

_embedding_fn = None


def get_embedding_fn() -> OpenAIEmbeddingFunction:
    """百炼(兼容 OpenAI 协议)的向量模型，懒加载，避免 import 阶段就崩"""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = OpenAIEmbeddingFunction(
            api_key=settings.BAILIAN_API_KEY,
            model_name=settings.BAILIAN_VECTOR_MODEL,
            api_base=settings.BAILIAN_BASE_URL,
        )
    return _embedding_fn


def get_collection() -> Collection:
    global _collection
    if _collection is not None:
        return _collection
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=get_embedding_fn())
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding='UTF-8').strip()
            if not text:
                continue
            docs.append(text)
            ids.append(path.stem)
            metas.append({'source': path.name})
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)
    _collection = col
    return _collection


def warmup():
    col = get_collection()
    if col.count() > 0:
        col.query(query_texts=['预热'], n_results=1)


def search(query: str):
    col = get_collection()
    if col.count() == 0:
        return ""
    limit = min(5, col.count())
    res = col.query(query_texts=[query], n_results=limit)
    docs = (res.get("documents") or [[]])[0]  #[list]
    metas = (res.get("metadatas") or [[]])[0]  #[list]
    distances = (res.get("distances") or [[]])[0]  #[list]
    score_parts = []
    for doc, metas, dist in zip(docs, metas, distances):
        score = 1 / (1 + dist)
        # if score < 0.5:
        #     continue
        name = metas.get("source") or ""
        score_parts.append({"score": score, "content": f"[{name}]\n{doc}"})
    print('检索出的score_parts', score_parts)
    score_parts.sort(key=lambda x: x["score"], reverse=True)
    final_parts = [item["content"] for item in score_parts[:2]]
    return "\n\n".join(final_parts)
