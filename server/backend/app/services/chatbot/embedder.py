# src/embedder.py
import google.generativeai as genai
from typing import List
import time

class GeminiEmbedder:
    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        genai.configure(api_key=api_key)
        self.model_name = model_name
    
    def embed_text(self, text: str) -> List[float]:
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Erreur embedding: {e}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self.embed_text(text)
            if embedding:
                embeddings.append(embedding)
            time.sleep(0.5)  # Rate limiting
        return embeddings