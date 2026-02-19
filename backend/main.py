from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import re

from .database import engine, Base, get_db, SessionLocal
from .models import Memory
from .rag import rag

# --------------------------------------------------
# Create Database Tables
# --------------------------------------------------
Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# Initialize FastAPI
# --------------------------------------------------
app = FastAPI(title="MindCare AI")

# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Request Schemas
# --------------------------------------------------
class MemoryCreate(BaseModel):
    content: str


class QueryRequest(BaseModel):
    query: str


# --------------------------------------------------
# Perspective Rewriter
# --------------------------------------------------
def rewrite_perspective(text: str) -> str:
    replacements = {
        r"\bmy\b": "your",
        r"\bMy\b": "Your",
        r"\bi\b": "you",
        r"\bI\b": "You",
        r"\bI'm\b": "You're",
        r"\bam\b": "are",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text


# --------------------------------------------------
# Detect History Intent
# --------------------------------------------------
def is_history_query(query: str) -> bool:
    keywords = [
        "before",
        "earlier",
        "previously",
        "history",
        "initially",
        "past"
    ]
    query_lower = query.lower()
    return any(word in query_lower for word in keywords)


# --------------------------------------------------
# Robust Object Extraction (Fixes punctuation issue)
# --------------------------------------------------
def extract_object_from_query(query: str):
    match = re.search(r"\bmy\s+(\w+)", query.lower())
    if match:
        return match.group(1)
    return None


# --------------------------------------------------
# Extract Location Phrase
# --------------------------------------------------
def extract_location(text: str):
    keywords = ["in ", "on ", "inside ", "near ", "at ", "to "]

    lower_text = text.lower()

    for key in keywords:
        if key in lower_text:
            start_index = lower_text.find(key)
            return text[start_index:].strip().capitalize()

    return None


# --------------------------------------------------
# Startup: Load Existing Memories into FAISS
# --------------------------------------------------
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        memories = db.query(Memory).all()

        if memories:
            rag.rebuild_index(memories)
            print(f"Loaded {len(memories)} memories into RAG index.")
        else:
            print("No memories found in database.")
    finally:
        db.close()


# --------------------------------------------------
# Health Check
# --------------------------------------------------
@app.get("/")
def root():
    return {"message": "MindCare backend is running successfully"}


# --------------------------------------------------
# Add Memory
# --------------------------------------------------
@app.post("/add_memory")
def add_memory(memory: MemoryCreate, db: Session = Depends(get_db)):
    db_memory = Memory(content=memory.content)
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)

    rag.add_memory(db_memory.content)

    return {
        "message": "Memory added successfully",
        "id": db_memory.id
    }


# --------------------------------------------------
# Ask Question
# --------------------------------------------------
@app.post("/ask")
def ask(request: QueryRequest, db: Session = Depends(get_db)):

    # Step 1: Semantic Search
    results = rag.search(request.query, top_k=5, threshold=1.5)

    if not results:
        return {"response": "I don't recall anything about that."}

    # Step 2: Get DB records ordered by newest
    matched_memories = (
        db.query(Memory)
        .filter(Memory.content.in_(results))
        .order_by(Memory.timestamp.desc())
        .all()
    )

    if not matched_memories:
        return {"response": "I don't recall anything about that."}

    # Step 3: Object-Level Filtering
    object_keyword = extract_object_from_query(request.query)

    if object_keyword:
        matched_memories = [
            memory for memory in matched_memories
            if object_keyword in memory.content.lower()
        ]

    if not matched_memories:
        return {"response": "I don't recall anything about that."}

    # --------------------------------------------------
    # HISTORY MODE (Last 3 States)
    # --------------------------------------------------
    if is_history_query(request.query):

        limited_memories = matched_memories[:3]
        limited_memories = list(reversed(limited_memories))

        history_responses = []
        labels = ["Earlier", "Then", "Now"]

        for i, memory in enumerate(limited_memories):
            rewritten = rewrite_perspective(memory.content)
            location = extract_location(rewritten)

            if location:
                history_responses.append(f"{labels[i]}: {location}")
            else:
                history_responses.append(f"{labels[i]}: {rewritten}")

        return {
            "response": "Recent memory history:\n" +
                        "\n".join(history_responses)
        }

    # --------------------------------------------------
    # DEFAULT MODE (Latest State Only)
    # --------------------------------------------------
    latest_memory = matched_memories[0].content
    rewritten = rewrite_perspective(latest_memory)

    return {"response": rewritten}
