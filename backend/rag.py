import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class RAG:
    def __init__(self):
        # Load embedding model
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # Determine embedding dimension dynamically
        dummy_embedding = self.encoder.encode(["test"])
        self.dimension = len(dummy_embedding[0])

        # FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)

        # Store raw memory texts
        self.memories = []

    # ---------------------------------------------------
    # Add single memory
    # ---------------------------------------------------
    def add_memory(self, text: str):
        if not text:
            return

        embedding = self.encoder.encode([text])
        embedding = np.array(embedding).astype("float32")

        self.index.add(embedding)
        self.memories.append(text)

    # ---------------------------------------------------
    # Rebuild index from database at startup
    # ---------------------------------------------------
    def rebuild_index(self, memory_objects):
        """
        memory_objects = list of DB Memory rows
        """
        self.index.reset()
        self.memories = []

        if not memory_objects:
            return

        texts = [m.content for m in memory_objects]
        embeddings = self.encoder.encode(texts)
        embeddings = np.array(embeddings).astype("float32")

        self.index.add(embeddings)
        self.memories.extend(texts)

    # ---------------------------------------------------
    # Semantic Search
    # ---------------------------------------------------
    def search(self, query: str, top_k: int = 3, threshold: float = 1.5):
        """
        Returns list of relevant memory strings.
        Uses L2 distance (lower = more similar).
        """

        if not self.memories or self.index.ntotal == 0:
            return []

        # Encode query
        query_vector = self.encoder.encode([query])
        query_vector = np.array(query_vector).astype("float32")

        # Search FAISS
        distances, indices = self.index.search(query_vector, top_k)

        matches = []

        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:
                continue

            # Apply similarity threshold
            if distance <= threshold:
                matches.append(self.memories[int(idx)])

        return matches


# Singleton instance
rag = RAG()
