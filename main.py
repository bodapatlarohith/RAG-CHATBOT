import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from transcript_fetcher import fetch_video_data
from vector_store import ingest_video, reset_vectorstore
from rag_chain import get_rag_chain, reset_rag_chain

app = FastAPI(title="Video RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for video metadata (for /videos endpoint)
_video_store: dict = {}


class IngestRequest(BaseModel):
    url_a: str
    url_b: str


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {"status": "ok", "message": "Video RAG API running"}


@app.post("/ingest")
async def ingest(req: IngestRequest):
    global _video_store

    try:
        print(f"Fetching Video A: {req.url_a}")
        data_a = await asyncio.to_thread(fetch_video_data, req.url_a)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch Video A: {str(e)}")

    try:
        print(f"Fetching Video B: {req.url_b}")
        data_b = await asyncio.to_thread(fetch_video_data, req.url_b)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch Video B: {str(e)}")

    # Reset stores for fresh session
    reset_vectorstore()
    chain = reset_rag_chain()

    # Ingest both videos
    chunks_a = ingest_video(data_a, "A")
    chunks_b = ingest_video(data_b, "B")

    # Set metadata on chain
    chain.set_video_metadata("A", data_a)
    chain.set_video_metadata("B", data_b)

    # Store for /videos endpoint
    _video_store = {"A": data_a, "B": data_b}

    return {
        "status": "success",
        "video_a": {
            "title": data_a["title"],
            "creator": data_a["creator"],
            "views": data_a["views"],
            "likes": data_a["likes"],
            "comments": data_a["comments"],
            "engagement_rate": data_a["engagement_rate"],
            "duration_seconds": data_a["duration_seconds"],
            "platform": data_a["platform"],
            "chunks_ingested": chunks_a,
        },
        "video_b": {
            "title": data_b["title"],
            "creator": data_b["creator"],
            "views": data_b["views"],
            "likes": data_b["likes"],
            "comments": data_b["comments"],
            "engagement_rate": data_b["engagement_rate"],
            "duration_seconds": data_b["duration_seconds"],
            "platform": data_b["platform"],
            "chunks_ingested": chunks_b,
        },
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    chain = get_rag_chain()

    async def generate():
        async for token in chain.stream_response(req.message):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/videos")
def get_videos():
    if not _video_store:
        return {"videos": {}}
    return {
        "videos": {
            label: {
                "title": v["title"],
                "creator": v["creator"],
                "platform": v["platform"],
                "views": v["views"],
                "likes": v["likes"],
                "comments": v["comments"],
                "engagement_rate": v["engagement_rate"],
                "duration_seconds": v["duration_seconds"],
                "upload_date": v["upload_date"],
                "hashtags": v["hashtags"][:10],
                "url": v["url"],
            }
            for label, v in _video_store.items()
        }
    }


@app.post("/chat/reset")
def reset_chat():
    reset_rag_chain()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
