"""
RAG Service Module

Provides a service interface to the existing RAG infrastructure
for document upload, processing, and retrieval.

This module wraps the existing Docling processor and VectorStore
to make them available via API endpoints.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from backend.rag.docling_processor import DoclingProcessor
from backend.rag.vector_store import VectorStore


class RAGService:
    """
    Service interface for RAG operations

    Wraps existing RAG infrastructure (DoclingProcessor and VectorStore)
    to provide clean API for document upload and retrieval operations.
    """

    def __init__(
        self,
        api_key: str,
        upload_dir: str = "backend/data/documents",
        vector_db_path: str = "backend/data/vector_db/faiss_index",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize RAG service

        Args:
            api_key: API key for embeddings (kept for compatibility)
            upload_dir: Directory to store uploaded files
            vector_db_path: Path to FAISS vector database
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Initialize document processor (uses existing Docling)
        self.processor = DoclingProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Initialize vector store (uses existing FAISS setup)
        self.vector_store = VectorStore(
            api_key=api_key,
            embedding_dimension=384,
            index_path=vector_db_path
        )

        # Load existing vector store if available
        self.vector_store.load()

    def upload_and_process_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload and process a document into the RAG system

        Args:
            file_content: Raw file bytes
            filename: Original filename
            user_id: ID of user uploading the document
            metadata: Optional additional metadata

        Returns:
            Dict with upload results and processing info
        """
        # Generate unique filename to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = self.upload_dir / safe_filename

        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Process document with Docling processor
        try:
            chunks = self.processor.process_document(str(file_path))

            if not chunks:
                return {
                    "success": False,
                    "error": "Failed to extract content from document",
                    "filename": filename
                }

            # Add user metadata to all chunks
            for chunk in chunks:
                chunk.metadata.update({
                    "uploaded_by": user_id,
                    "upload_timestamp": timestamp,
                    "original_filename": filename
                })

                # Add any custom metadata provided
                if metadata:
                    chunk.metadata.update(metadata)

            # Add chunks to vector store
            self.vector_store.add_documents(chunks)

            # Save updated vector store
            self.vector_store.save()

            return {
                "success": True,
                "filename": filename,
                "saved_as": safe_filename,
                "file_path": str(file_path),
                "chunks_created": len(chunks),
                "file_size": len(file_content),
                "message": f"Successfully processed {filename} into {len(chunks)} chunks"
            }

        except Exception as e:
            # Clean up file if processing failed
            if file_path.exists():
                file_path.unlink()

            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def search_documents(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for relevant document chunks

        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Optional similarity threshold

        Returns:
            List of relevant chunks with metadata
        """
        results = self.vector_store.search(
            query=query,
            k=k,
            score_threshold=score_threshold
        )

        # Format results
        formatted_results = []
        for chunk_dict, score in results:
            formatted_results.append({
                "content": chunk_dict["content"],
                "metadata": chunk_dict["metadata"],
                "score": score,
                "chunk_id": chunk_dict["chunk_id"]
            })

        return formatted_results

    def list_uploaded_documents(self) -> List[Dict]:
        """
        List all documents that have been uploaded via this service

        Returns:
            List of document info dictionaries
        """
        documents = []

        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": stat.st_size,
                    "upload_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "file_type": file_path.suffix[1:] if file_path.suffix else "unknown"
                })

        # Sort by upload date (newest first)
        documents.sort(key=lambda x: x["upload_date"], reverse=True)

        return documents

    def get_vector_store_stats(self) -> Dict:
        """
        Get statistics about the vector store

        Returns:
            Dict with vector store statistics
        """
        return {
            "total_chunks": len(self.vector_store.chunks),
            "embedding_dimension": self.vector_store.embedding_dimension,
            "index_path": str(self.vector_store.index_path),
            "uploaded_documents_count": len(list(self.upload_dir.glob("*")))
        }

    def delete_document(self, document_id: str) -> Dict:
        """
        Delete a document from the RAG system
        
        Removes the document file from disk and its associated chunks
        from the vector store.
        
        Args:
            document_id: The filename/identifier of the document to delete
            
        Returns:
            Dict with success status and deletion details
        """
        # Find the document file - document_id could be the full filename or partial
        matching_files = []
        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                # Check if document_id matches the filename (full or partial)
                if document_id == file_path.name or document_id in file_path.name:
                    matching_files.append(file_path)
        
        if not matching_files:
            return {
                "success": False,
                "error": f"Document '{document_id}' not found",
                "deleted_chunks": 0
            }
        
        # Use the first matching file (most specific match)
        file_path = matching_files[0]
        filename = file_path.name
        
        # Delete chunks from vector store first
        delete_result = self.vector_store.delete_by_source(filename)
        
        # Check if vector store deletion succeeded before deleting the file
        # This prevents orphaned chunks if metadata doesn't match
        if not delete_result.get("success", False):
            return {
                "success": False,
                "error": f"No chunks found for document '{filename}' in vector store",
                "deleted_chunks": 0,
                "message": delete_result.get("message", "Metadata mismatch - file not deleted to prevent orphaned state")
            }
        
        # Delete the physical file from disk only after successful chunk deletion
        try:
            file_path.unlink()
            print(f"✅ Deleted file: {filename}")
        except Exception as e:
            print(f"⚠️  Warning: Could not delete file {filename}: {e}")
            # Chunks were deleted but file remains - still report partial success
            return {
                "success": True,
                "deleted_file": filename,
                "deleted_chunks": delete_result.get("deleted_chunks", 0),
                "remaining_chunks": delete_result.get("remaining_chunks", len(self.vector_store.chunks)),
                "warning": f"Chunks deleted but file could not be removed: {e}"
            }
        
        # Save updated vector store
        self.vector_store.save()
        
        return {
            "success": True,
            "deleted_file": filename,
            "deleted_chunks": delete_result.get("deleted_chunks", 0),
            "remaining_chunks": delete_result.get("remaining_chunks", len(self.vector_store.chunks))
        }


# Singleton instance (initialized by FastAPI at startup)
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create the RAG service singleton

    Returns:
        RAGService instance
    """
    global _rag_service

    if _rag_service is None:
        # Get API key from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        _rag_service = RAGService(api_key=api_key)

    return _rag_service


def initialize_rag_service(api_key: str) -> RAGService:
    """
    Explicitly initialize the RAG service (called by FastAPI on startup)

    Args:
        api_key: API key for embeddings

    Returns:
        Initialized RAGService instance
    """
    global _rag_service
    _rag_service = RAGService(api_key=api_key)
    return _rag_service
