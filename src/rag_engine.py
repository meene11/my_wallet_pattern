"""
RAG 소비 코칭 엔진
- data/knowledge/ 의 마크다운 문서를 ChromaDB에 인덱싱
- 유저 소비 패턴과 유사한 문서를 검색하여 GPT 프롬프트에 주입
"""
import os
import glob
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", ".chromadb")
COLLECTION_NAME = "spending_coaching"

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection

    api_key = os.getenv("OPENAI_API_KEY")
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    # 문서가 없으면 인덱싱
    if _collection.count() == 0:
        _index_documents(_collection)

    return _collection


def _index_documents(collection):
    """data/knowledge/ 의 .md 파일을 청크 단위로 ChromaDB에 저장"""
    md_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md"))
    documents, metadatas, ids = [], [], []

    for path in md_files:
        filename = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()

        # 섹션(##) 단위로 청크 분할
        chunks = _split_by_section(content)
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 30:
                continue
            doc_id = f"{filename}_{i}"
            documents.append(chunk)
            metadatas.append({"source": filename})
            ids.append(doc_id)

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)


def _split_by_section(text: str) -> list[str]:
    """## 헤더 기준으로 텍스트를 청크로 분할"""
    lines = text.split("\n")
    chunks, current = [], []
    for line in lines:
        if line.startswith("## ") and current:
            chunks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


def retrieve_coaching_context(query: str, n_results: int = 2) -> str:
    """
    유저 소비 패턴 쿼리와 유사한 코칭 문서를 검색하여 텍스트로 반환.
    GPT 프롬프트에 컨텍스트로 주입하기 위한 용도.
    """
    try:
        collection = _get_collection()
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""
        return "\n\n---\n\n".join(docs)
    except Exception:
        return ""


def reset_index():
    """인덱스를 초기화하고 재구축 (문서 변경 시 사용)"""
    global _collection
    api_key = os.getenv("OPENAI_API_KEY")
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )
    _index_documents(_collection)
