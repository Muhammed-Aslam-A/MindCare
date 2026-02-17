from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


class RAGSystem:
    def __init__(self):
        # Load embedding model (384-dimension output)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # Create FAISS L2 index
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)

        # Store original memory texts
        self.memories = []

    def add_memory(self, text: str):
        """
        Add a single memory to the FAISS index
        """
        if not text:
            return

        # Encode text
        vector = self.encoder.encode([text])
        vector = np.array(vector).astype("float32")

        # Add to index
        self.index.add(vector)

        # Store raw text
        self.memories.append(text)

    def rebuild_index(self, memories):
        """
        Rebuild index from database records
        Accepts either:
        - List of Memory objects
        - List of strings
        """
        self.index.reset()
        self.memories = []

        if not memories:
            return

        # Extract text content
        texts = [
            m.content if hasattr(m, "content") else m
            for m in memories
        ]

        if not texts:
            return

        # Encode all texts
        vectors = self.encoder.encode(texts)
        vectors = np.array(vectors).astype("float32")

        # Add to FAISS
        self.index.add(vectors)

        # Store texts
        self.memories = texts

    def search(self, query: str, k: int = 1, threshold: float = 1.5):
        """
        Search most relevant memory using L2 similarity.
        Lower distance = more similar.
        """

        # If index empty
        if not self.memories or self.index.ntotal == 0:
            return None

        # Encode query
        query_vector = self.encoder.encode([query])
        query_vector = np.array(query_vector).astype("float32")

        # Perform search
        D, I = self.index.search(query_vector, k)

        # Safety checks
        if len(I) == 0 or len(I[0]) == 0:
            return None

        index = int(I[0][0])
        distance = float(D[0][0])

        # Invalid index
        if index == -1:
            return None

        # Reject weak matches
        if distance > threshold:
            return None

        return self.memories[index]


# Singleton instance
rag = RAGSystem()
