from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class RAGSystem:
    def __init__(self):
        # efficient, small model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        # 384 dimensions for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(384)
        self.memories = []

    def add_memory(self, text):
        vector = self.encoder.encode([text])
        self.index.add(np.array(vector).astype('float32'))
        self.memories.append(text)

    def rebuild_index(self, memories):
        """Rebuild index from a list of Memory objects or strings"""
        self.index.reset()
        self.memories = []
        
        if not memories:
            return

        # Extract text content if they are objects, else assume strings
        texts = [m.content if hasattr(m, 'content') else m for m in memories]
        
        if not texts:
            return

        vectors = self.encoder.encode(texts)
        self.index.add(np.array(vectors).astype('float32'))
        self.memories = texts

    def search(self, query, k=1):
        if not self.memories:
            return None
        
        query_vector = self.encoder.encode([query])
        D, I = self.index.search(np.array(query_vector).astype('float32'), k)
        
        if I[0][0] == -1:
            return None
        
        return self.memories[I[0][0]]

# Singleton instance
rag = RAGSystem()
