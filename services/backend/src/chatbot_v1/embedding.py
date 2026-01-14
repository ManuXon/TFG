from langchain.embeddings.base import Embeddings
from typing import List
from openai import OpenAI
import os


class CustomEmbedding(Embeddings):
    """Custom embedding using OpenAI's text-embedding-3-small model"""

    def __init__(self, api_key: str = None):
        """Initialize OpenAI client for embeddings"""
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        # OpenAI supports batch embeddings
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        response = self.client.embeddings.create(
            input=[text],
            model=self.model
        )
        return response.data[0].embedding
