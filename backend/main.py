from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import engine, Base, get_db, SessionLocal
from models import Memory
from rag import rag

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MindCare AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MemoryCreate(BaseModel):
    content: str

@app.on_event("startup")
def startup_event():
    # Load memories from DB to rebuild index
    db = SessionLocal()
    try:
        memories = db.query(Memory).all()
        rag.rebuild_index(memories)
        
        # If DB is empty, add a default memory to avoid FAISS errors if any
        if not memories:
            print("No memories found in DB.")
        else:
            print(f"Loaded {len(memories)} memories into RAG index.")
    finally:
        db.close()

@app.post("/add_memory")
def add_memory(memory: MemoryCreate, db: Session = Depends(get_db)):
    db_memory = Memory(content=memory.content)
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    
    # Update RAG
    rag.add_memory(db_memory.content)
    
    return {"message": "Memory added", "id": db_memory.id}

@app.get("/ask")
def ask(query: str):
    result = rag.search(query)
    if result:
        return {"response": result}
    else:
        return {"response": "I don't recall anything about that."}
