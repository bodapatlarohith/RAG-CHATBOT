import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.documents import Document

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
COLLECTION_NAME = "video_transcripts"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size

_embeddings = None
_client = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        print("Loading local embedding model (first time ~30 seconds)...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        print("Embedding model loaded!")
    return _embeddings


def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(":memory:")
    return _client


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        client = get_client()
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
        _vectorstore = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=get_embeddings(),
        )
    return _vectorstore


def reset_vectorstore():
    global _client, _vectorstore
    _client = QdrantClient(":memory:")
    _client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    _vectorstore = QdrantVectorStore(
        client=_client,
        collection_name=COLLECTION_NAME,
        embedding=get_embeddings(),
    )


def ingest_video(video_data: dict, label: str) -> int:
    vs = get_vectorstore()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    transcript = video_data.get("transcript", "")
    metadata_summary = _build_metadata_summary(video_data, label)
    transcript_chunks = splitter.split_text(transcript) if transcript else []

    docs: List[Document] = []
    docs.append(Document(
        page_content=metadata_summary,
        metadata={
            "video_id": label,
            "platform": video_data["platform"],
            "creator": video_data["creator"],
            "chunk_type": "metadata",
            "source": f"Video {label} - Metadata",
        },
    ))
    for i, chunk in enumerate(transcript_chunks):
        docs.append(Document(
            page_content=chunk,
            metadata={
                "video_id": label,
                "platform": video_data["platform"],
                "creator": video_data["creator"],
                "chunk_type": "transcript",
                "chunk_index": i,
                "source": f"Video {label} - Transcript (chunk {i + 1})",
            },
        ))
    vs.add_documents(docs)
    return len(docs)


def _build_metadata_summary(v: dict, label: str) -> str:
    hashtags = v.get("hashtags", [])
    return (
        f"Video {label} Metadata Summary\n"
        f"Platform: {v.get('platform', 'unknown')}\n"
        f"Title: {v.get('title', 'N/A')}\n"
        f"Creator: {v.get('creator', 'N/A')}\n"
        f"Follower Count: {v.get('follower_count', 'N/A')}\n"
        f"Views: {v.get('views', 0):,}\n"
        f"Likes: {v.get('likes', 0):,}\n"
        f"Comments: {v.get('comments', 0):,}\n"
        f"Duration: {v.get('duration_seconds', 0)}s\n"
        f"Upload Date: {v.get('upload_date', 'N/A')}\n"
        f"Hashtags: {', '.join(hashtags[:10])}\n"
        f"Engagement Rate: {v.get('engagement_rate', 0)}%\n"
        f"Description: {v.get('description', '')[:300]}"
    ).strip()


def similarity_search(query: str, k: int = 6) -> List[Document]:
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)
