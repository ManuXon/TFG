from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from typing import List


class MarkdownSplitter:
    """Split markdown documentation by headers into Document chunks"""

    def __init__(self):
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "section"),
                ("##", "subsection"),
            ],
            return_each_line=False
        )

    def split_text(self, markdown_str: str) -> List[Document]:
        """
        Split markdown text into Document chunks based on headers

        Args:
            markdown_str: Full markdown text content

        Returns:
            List of Document objects with section/subsection metadata
        """
        # Split returns proper Document objects
        docs = self.splitter.split_text(markdown_str)

        # Ensure all are proper Document objects
        result = []
        for i, doc in enumerate(docs):
            try:
                # If it's already a Document, use it
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    result.append(Document(
                        page_content=doc.page_content,
                        metadata=doc.metadata or {}
                    ))
                else:
                    # Fallback: treat as string
                    result.append(Document(
                        page_content=str(doc),
                        metadata={"chunk": i}
                    ))
            except Exception as e:
                print(f"⚠️ Warning converting document {i}: {e}")
                # Last resort: create simple document
                result.append(Document(
                    page_content=str(doc),
                    metadata={"chunk": i, "error": str(e)}
                ))

        return result
