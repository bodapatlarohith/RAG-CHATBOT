import os
import json
from typing import AsyncGenerator, List
from groq import Groq
from langchain_core.documents import Document
from vector_store import similarity_search

GROQ_MODEL = "llama-3.1-70b-versatile"

SYSTEM_PROMPT = """You are a social media video analytics expert helping creators understand their content performance.

You have access to transcripts and metadata from two videos (Video A and Video B).
Use the provided context chunks to answer questions accurately.

Rules:
1. Always cite your sources using [Video X - chunk type] format inline.
2. When comparing engagement, use the actual numbers from the metadata.
3. For hook analysis, focus on transcript content from the first portion of the transcript.
4. Be specific, data-driven, and actionable.
5. If context doesn't contain the answer, say so clearly.

Context from vector database:
{context}
"""


class RAGChain:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.conversation_history: List[dict] = []
        self.video_metadata: dict = {}

    def set_video_metadata(self, label: str, metadata: dict):
        self.video_metadata[label] = metadata

    def clear_history(self):
        self.conversation_history = []

    def _format_docs(self, docs: List[Document]) -> str:
        parts = []
        for doc in docs:
            src = doc.metadata.get("source", "unknown")
            parts.append(f"[{src}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    def _retrieve_context(self, query: str):
        docs = similarity_search(query, k=8)
        return self._format_docs(docs), docs

    async def stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        context_str, source_docs = self._retrieve_context(user_message)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context_str)}
        ]
        # Add last 8 turns of history
        for msg in self.conversation_history[-8:]:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        full_response = ""

        # Groq streaming
        stream = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            stream=True,
            temperature=0.3,
            max_tokens=1024,
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                full_response += token
                yield token

        # Save to history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": full_response})

        # Send sources at end
        sources = []
        seen = set()
        for doc in source_docs:
            src = doc.metadata.get("source", "")
            if src and src not in seen:
                seen.add(src)
                sources.append({
                    "source": src,
                    "video_id": doc.metadata.get("video_id", ""),
                    "chunk_type": doc.metadata.get("chunk_type", ""),
                    "preview": doc.page_content[:120] + "...",
                })
        yield f"\n\n__SOURCES__{json.dumps(sources)}__END_SOURCES__"


_chain: RAGChain = None


def get_rag_chain() -> RAGChain:
    global _chain
    if _chain is None:
        _chain = RAGChain()
    return _chain


def reset_rag_chain():
    global _chain
    _chain = RAGChain()
    return _chain
