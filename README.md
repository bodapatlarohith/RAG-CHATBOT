# 🎬 Video RAG Analyser

> An AI-powered full stack application that analyses and compares two YouTube or Instagram videos using Retrieval-Augmented Generation (RAG). Paste two video URLs, and chat with an AI that knows everything about both videos — transcripts, engagement, hooks, hashtags, and more.

---

## 📄 Project Overview

**Objective:**
Help content creators and social media analysts compare video performance by combining real video metadata and transcripts with a RAG pipeline powered by Groq's LLaMA 3.1 70B model.

---

## ✨ Key Features

- 🔗 **Multi-Platform Support** — Accepts YouTube and Instagram video URLs
- 📊 **Engagement Metrics** — Views, likes, comments, engagement rate, duration
- 📜 **Transcript Ingestion** — Fetches real transcripts using YouTube Transcript API
- 🧠 **RAG Pipeline** — Semantic search over video chunks using Qdrant + all-MiniLM-L6-v2
- 💬 **Streaming Chat** — Real-time AI responses via Groq LLaMA 3.1 70B (Server-Sent Events)
- 🔍 **Comparison Analysis** — Ask anything: hooks, hashtags, engagement, improvements
- ⚡ **Fast & Local Embeddings** — No OpenAI needed for embeddings

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                      │
│   Paste Video URLs → View Metrics → Chat with AI    │
└───────────────────────┬─────────────────────────────┘
                        │ REST API + SSE Streaming
┌───────────────────────▼─────────────────────────────┐
│               FastAPI Backend                        │
│   /ingest   /chat   /videos   /chat/reset            │
└──────────────┬───────────────────────┬──────────────┘
               │                       │
┌──────────────▼──────────┐  ┌────────▼──────────────┐
│   Transcript Fetcher     │  │     RAG Chain          │
│   yt-dlp + YouTube       │  │   Groq LLaMA 3.1 70B  │
│   Transcript API         │  │   Streaming Response   │
│   Instagram via yt-dlp   │  │   Conversation History │
└──────────────┬──────────┘  └────────┬──────────────┘
               │                       │
┌──────────────▼───────────────────────▼──────────────┐
│              Vector Store (Qdrant In-Memory)          │
│   all-MiniLM-L6-v2 Embeddings (384-dim)              │
│   Metadata Chunks + Transcript Chunks                 │
│   Cosine Similarity Search (k=8)                     │
└──────────────────────────────────────────────────────┘
```

---

## 💡 How It Works

1. **Input** — User pastes two YouTube or Instagram video URLs
2. **Fetch** — `yt-dlp` fetches metadata; YouTube Transcript API fetches transcripts
3. **Chunk** — Transcripts are split into 500-token chunks with 50-token overlap
4. **Embed** — All chunks are embedded using `all-MiniLM-L6-v2` and stored in Qdrant
5. **Chat** — User asks a question; top 8 relevant chunks are retrieved
6. **Generate** — Groq LLaMA 3.1 70B generates a streamed response with citations
7. **Display** — Response streams in real-time with source references

---

## 🛠️ Technologies Used

| Layer | Technology |
|-------|-----------|
| **Frontend** | React.js, Vite |
| **Backend** | Python, FastAPI, Uvicorn |
| **LLM** | Groq — LLaMA 3.1 70B Versatile |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Vector DB** | Qdrant (in-memory) |
| **RAG Framework** | LangChain, LangChain-HuggingFace |
| **Video Data** | yt-dlp, YouTube Transcript API |
| **Streaming** | Server-Sent Events (SSE) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (free at [console.groq.com](https://console.groq.com))
- `yt-dlp` installed globally

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/bodapatlarohith/video-rag-analyser.git
cd video-rag-analyser
```

**2. Backend setup**
```bash
cd backend
pip install -r requirements.txt
```

**3. Create `.env` file in backend folder**
```
GROQ_API_KEY=your_groq_api_key_here
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

**4. Run backend**
```bash
uvicorn main:app --reload --port 8000
```
✅ Backend runs on `http://localhost:8000`

**5. Frontend setup**
```bash
cd frontend
npm install
npm run dev
```
✅ Frontend runs on `http://localhost:5173`

---

## 💬 Example Questions to Ask

- *"Which video had better engagement and why?"*
- *"What hashtags performed best?"*
- *"Compare the hooks of both videos"*
- *"How can Video B improve its retention?"*
- *"What topics did both creators focus on?"*

---

## 📁 Project Structure

```
video-rag-analyser/
├── backend/
│   ├── main.py                 # FastAPI app & routes
│   ├── transcript_fetcher.py   # yt-dlp + YouTube Transcript API
│   ├── vector_store.py         # Qdrant + embeddings + ingestion
│   ├── rag_chain.py            # Groq LLM + RAG + streaming
│   ├── requirements.txt
│   └── .env                    # GROQ_API_KEY (not committed)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component
│   │   └── main.jsx
│   └── package.json
├── screenshots/
│   ├── home.png
│   └── analysis.png
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key (free) |
| `CHUNK_SIZE` | Token size per chunk (default: 500) |
| `CHUNK_OVERLAP` | Overlap between chunks (default: 50) |

---

## 📸 Demo — Screenshots & Video

### Home Page — Enter Video URLs
<img width="1677" height="909" alt="Home Page" src="https://github.com/user-attachments/assets/3cd0f35a-79cc-47a6-a097-f668e23e8d6e" />

### Analysis Page — Metrics + AI Chat
<img width="1679" height="923" alt="Analysis Page" src="https://github.com/user-attachments/assets/3e9d6d34-7e84-4597-8f5a-e65d42c08935" />

### 🎥 Video Walkthrough

https://github.com/user-attachments/assets/9e714b71-9d19-4ee8-be09-c2cbef62cda1

---

## 🙋 Author

**Rohit**
📧 bodapatlarohithkumar7@gmail.com
📱 7981158530
🔗 GitHub: [github.com/bodapatlarohith](https://github.com/bodapatlarohith)
