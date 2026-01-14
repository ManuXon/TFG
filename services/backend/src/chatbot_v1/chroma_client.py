import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from .embedding import CustomEmbedding
from typing import List
from langchain_core.documents import Document  # Use langchain_core
from uuid import uuid4

import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


class ChromaClient:
    """Vector database client for storing and retrieving dataset information"""

    def __init__(self, persist_path: str = "./chatbot_db", collection_name: str = "mapai_dataset", api_key: str = None):
        # Create the raw Chroma client & collection handle
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(name=collection_name)

        # Wrap it in LangChain's Chroma vector store with OpenAI embeddings
        self.vector_store = Chroma(
            client=self._client,
            collection_name=collection_name,
            embedding_function=CustomEmbedding(api_key=api_key),
            persist_directory=persist_path
        )

    def is_empty(self) -> bool:
        """Return True if there are zero vectors in the collection"""
        return self._collection.count() == 0

    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        # Ensure all documents are proper Document objects
        validated_docs = []
        for doc in documents:
            if isinstance(doc, Document):
                # Create a fresh Document to avoid _type issues
                validated_docs.append(
                    Document(
                        page_content=str(doc.page_content),
                        metadata=dict(doc.metadata) if doc.metadata else {}
                    )
                )
            else:
                # Convert to Document
                validated_docs.append(
                    Document(
                        page_content=str(doc),
                        metadata={}
                    )
                )

        # Generate UUIDs
        uuids = [str(uuid4()) for _ in validated_docs]

        # Add to vector store
        return self.vector_store.add_documents(documents=validated_docs, ids=uuids)

    def create_retriever(self, k: int = 10):
        """Create a retriever for querying the vector store"""
        return self.vector_store.as_retriever(search_kwargs={"k": k})
