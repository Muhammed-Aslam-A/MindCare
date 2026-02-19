from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .database import engine, Base, get_db, SessionLocal
from .models import Memory
from .rag import rag

# ----------------------------
# Create Database Tables
# ----------------------------
Base.metadata.create_all(bind=engine)

# ----------------------------
# Initialize FastAPI App
# ----------------------------
app = FastAPI(title="MindCare AI")

# ----------------------------
# CORS Configuration
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Request Schemas
# ----------------------------
class MemoryCreate(BaseModel):
    content: str


class QueryRequest(BaseModel):
    query: str


# ----------------------------
# Perspective Rewriter
# ----------------------------
def rewrite_perspective(text: str) -> str:
    replacements = {
        " my ": " your ",
        " My ": " Your ",
        " i ": " you ",
        " I ": " You ",
        " i'm ": " you're ",
        " I'm ": " You're ",
        " am ": " are ",
    }

    rewritten = f" {text} "
    for k, v in replacements.items():
        rewritten = rewritten.replace(k, v)

    return rewritten.strip()


# ----------------------------
# Startup Event
# ----------------------------
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


# ----------------------------
# Health Check
# ----------------------------
@app.get("/")
def root():
    return {"message": "MindCare backend is running successfully"}


# ----------------------------
# Add Memory
# ----------------------------
@app.post("/add_memory")
def add_memory(memory: MemoryCreate, db: Session = Depends(get_db)):
    db_memory = Memory(content=memory.content)
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)

    # Update RAG index
    rag.add_memory(db_memory.content)

    return {
        "message": "Memory added successfully",
        "id": db_memory.id
    }


# ----------------------------
# Ask Question (RAG Search)
# ----------------------------
@app.post("/ask")
def ask(request: QueryRequest):
    result = rag.search(request.query)

    if result:
        rewritten = rewrite_perspective(result)
        return {"response": rewritten}
    else:
        return {"response": "I don't recall anything about that."}
