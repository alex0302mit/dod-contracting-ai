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
            metadata: Optional additional metadata (project_id, phase, purpose, etc.)

        Returns:
            Dict with upload results, processing info, and chunk_ids for lineage tracking
        """
        import uuid
        
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

            # Generate unique chunk_ids for lineage tracking
            chunk_ids = []
            for idx, chunk in enumerate(chunks):
                # Generate a unique chunk_id using document + index
                chunk_id = f"{safe_filename}_chunk_{idx}_{uuid.uuid4().hex[:8]}"
                chunk_ids.append(chunk_id)
                
                # Add chunk_id to metadata for retrieval
                chunk.metadata.update({
                    "chunk_id": chunk_id,
                    "uploaded_by": user_id,
                    "upload_timestamp": timestamp,
                    "original_filename": filename,
                    "source_document": safe_filename,
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                })

                # Add any custom metadata provided (project_id, phase, purpose, etc.)
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
                "chunk_ids": chunk_ids,  # Return chunk_ids for lineage tracking
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
        score_threshold: Optional[float] = None,
        project_id: Optional[str] = None,
        phase: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for relevant document chunks with optional project/phase filtering
        
        Phase-aware search enables more relevant retrieval by prioritizing
        documents attached to the current phase of the acquisition workflow.

        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Optional similarity threshold
            project_id: Optional project ID to filter by
            phase: Optional phase to filter by (e.g., "pre_solicitation", "solicitation", "post_solicitation")

        Returns:
            List of relevant chunks with metadata
        """
        # Get more results initially if filtering will be applied
        # This ensures we still have enough results after filtering
        search_k = k * 3 if (project_id or phase) else k
        
        results = self.vector_store.search(
            query=query,
            k=search_k,
            score_threshold=score_threshold
        )

        # Format and filter results
        formatted_results = []
        phase_matched_results = []
        fallback_results = []
        
        for chunk_dict, score in results:
            chunk_metadata = chunk_dict.get("metadata", {})
            
            # Build result object
            result = {
                "content": chunk_dict["content"],
                "metadata": chunk_metadata,
                "score": score,
                "chunk_id": chunk_dict.get("chunk_id") or chunk_metadata.get("chunk_id")
            }
            
            # Apply project filter if specified
            if project_id:
                chunk_project = chunk_metadata.get("project_id")
                if chunk_project and chunk_project != project_id:
                    continue  # Skip chunks from different projects
            
            # Apply phase filter with fallback logic
            if phase:
                chunk_phase = chunk_metadata.get("phase")
                if chunk_phase == phase:
                    # Exact phase match - prioritize these
                    phase_matched_results.append(result)
                else:
                    # Different phase or no phase - keep as fallback
                    fallback_results.append(result)
            else:
                # No phase filter - include all
                formatted_results.append(result)
        
        # If phase filtering was applied, combine results with phase matches first
        if phase:
            # Log phase filtering for debugging
            print(f"[RAG] Phase filter '{phase}': {len(phase_matched_results)} matches, {len(fallback_results)} fallback")
            
            # Prioritize phase-matched results, then add fallbacks if needed
            formatted_results = phase_matched_results
            if len(formatted_results) < k:
                # Not enough phase matches - add fallbacks
                remaining_slots = k - len(formatted_results)
                formatted_results.extend(fallback_results[:remaining_slots])
        
        # Limit to requested number of results
        return formatted_results[:k]

    def get_documents_by_project(self, project_id: str) -> List[Dict]:
        """
        Get all document chunks associated with a specific project
        
        Args:
            project_id: Project ID to filter by
            
        Returns:
            List of unique documents (deduplicated from chunks) with metadata
        """
        documents = {}
        
        for chunk in self.vector_store.chunks:
            # Use helper to handle both dict and DocumentChunk objects
            chunk_data = self._get_chunk_data(chunk)
            chunk_metadata = chunk_data["metadata"]
            chunk_project = chunk_metadata.get("project_id")
            
            if chunk_project == project_id:
                source_doc = chunk_metadata.get("source_document") or chunk_metadata.get("source")
                if source_doc and source_doc not in documents:
                    documents[source_doc] = {
                        "filename": chunk_metadata.get("original_filename", source_doc),
                        "source_document": source_doc,
                        "project_id": project_id,
                        "phase": chunk_metadata.get("phase"),
                        "purpose": chunk_metadata.get("purpose"),
                        "uploaded_by": chunk_metadata.get("uploaded_by"),
                        "upload_timestamp": chunk_metadata.get("upload_timestamp"),
                        "chunk_count": 0,
                        "chunk_ids": []
                    }
                
                if source_doc:
                    documents[source_doc]["chunk_count"] += 1
                    chunk_id = chunk_data["chunk_id"]
                    if chunk_id:
                        documents[source_doc]["chunk_ids"].append(chunk_id)

        return list(documents.values())

    def get_documents_by_project_and_phase(self, project_id: str, phase: str) -> List[Dict]:
        """
        Get all document chunks for a specific project and phase
        
        Args:
            project_id: Project ID to filter by
            phase: Phase name (e.g., "pre_solicitation")
            
        Returns:
            List of unique documents matching project and phase
        """
        all_project_docs = self.get_documents_by_project(project_id)
        return [doc for doc in all_project_docs if doc.get("phase") == phase]

    def get_source_documents_for_chunks(self, chunk_ids: List[str]) -> List[Dict]:
        """
        Map chunk IDs back to their source documents for lineage tracking
        
        Args:
            chunk_ids: List of chunk IDs to look up
            
        Returns:
            List of unique source documents that contributed the given chunks
        """
        documents = {}
        chunk_id_set = set(chunk_ids)
        
        for chunk in self.vector_store.chunks:
            # Use helper to handle both dict and DocumentChunk objects
            chunk_data = self._get_chunk_data(chunk)
            chunk_metadata = chunk_data["metadata"]
            chunk_id = chunk_data["chunk_id"]
            
            if chunk_id in chunk_id_set:
                source_doc = chunk_metadata.get("source_document") or chunk_metadata.get("source")
                if source_doc and source_doc not in documents:
                    documents[source_doc] = {
                        "filename": chunk_metadata.get("original_filename", source_doc),
                        "source_document": source_doc,
                        "project_id": chunk_metadata.get("project_id"),
                        "phase": chunk_metadata.get("phase"),
                        "purpose": chunk_metadata.get("purpose"),
                        "chunk_ids_used": []
                    }
                
                if source_doc:
                    documents[source_doc]["chunk_ids_used"].append(chunk_id)
        
        return list(documents.values())

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> List[Dict]:
        """
        Get full chunk content and metadata by chunk IDs.
        
        Used for chunk-level traceability in the document lineage view,
        allowing users to see exactly what content influenced AI generation.
        
        Args:
            chunk_ids: List of chunk IDs to retrieve
            
        Returns:
            List of chunk dictionaries with content, metadata, and positional info
        """
        chunk_id_set = set(chunk_ids)
        results = []
        
        for chunk in self.vector_store.chunks:
            # Use helper to handle both dict and DocumentChunk objects
            chunk_data = self._get_chunk_data(chunk)
            chunk_id = chunk_data["chunk_id"]
            
            if chunk_id in chunk_id_set:
                chunk_metadata = chunk_data["metadata"]
                results.append({
                    "chunk_id": chunk_id,
                    "content": chunk_data["content"],
                    "source_document": chunk_metadata.get("source_document") or chunk_metadata.get("source"),
                    "original_filename": chunk_metadata.get("original_filename"),
                    "chunk_index": chunk_metadata.get("chunk_index", 0),
                    "total_chunks": chunk_metadata.get("total_chunks", 1),
                    "project_id": chunk_metadata.get("project_id"),
                    "phase": chunk_metadata.get("phase"),
                    "purpose": chunk_metadata.get("purpose"),
                    "metadata": chunk_metadata
                })
        
        # Sort by source document and chunk index for consistent ordering
        results.sort(key=lambda x: (x.get("source_document", ""), x.get("chunk_index", 0)))
        
        return results

    def _get_chunk_data(self, chunk) -> Dict:
        """
        Helper to safely extract data from a chunk (handles both dict and DocumentChunk object)
        
        Chunks can be either dictionaries or DocumentChunk dataclass objects depending on
        how they were loaded. This helper normalizes access.
        
        Args:
            chunk: Either a dict or DocumentChunk object
            
        Returns:
            Dict with 'content', 'metadata', and 'chunk_id' keys
        """
        if isinstance(chunk, dict):
            return {
                "content": chunk.get("content", ""),
                "metadata": chunk.get("metadata", {}),
                "chunk_id": chunk.get("chunk_id") or chunk.get("metadata", {}).get("chunk_id")
            }
        else:
            # DocumentChunk dataclass object - access via attributes
            return {
                "content": getattr(chunk, "content", ""),
                "metadata": getattr(chunk, "metadata", {}),
                "chunk_id": getattr(chunk, "chunk_id", None) or getattr(chunk, "metadata", {}).get("chunk_id")
            }

    def list_uploaded_documents(self) -> List[Dict]:
        """
        List all documents that have been uploaded via this service.
        
        Retrieves metadata from vector store chunks to include:
        - project_id, phase, purpose (for project-scoped documents)
        - chunk_ids for lineage tracking
        - uploaded_by and upload_timestamp

        Returns:
            List of document info dictionaries with full metadata
        """
        documents = []
        
        # Build a map of document metadata from vector store chunks
        # This gives us access to project_id, phase, purpose, etc.
        doc_metadata_map = {}
        for chunk in self.vector_store.chunks:
            # Use helper to handle both dict and DocumentChunk objects
            chunk_data = self._get_chunk_data(chunk)
            chunk_metadata = chunk_data["metadata"]
            source_doc = chunk_metadata.get("source_document") or chunk_metadata.get("source")
            if source_doc:
                if source_doc not in doc_metadata_map:
                    doc_metadata_map[source_doc] = {
                        "chunk_ids": [],
                        "metadata": chunk_metadata
                    }
                # Collect all chunk_ids for this document
                chunk_id = chunk_data["chunk_id"]
                if chunk_id:
                    doc_metadata_map[source_doc]["chunk_ids"].append(chunk_id)

        for file_path in self.upload_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                filename = file_path.name
                
                # Get metadata from vector store if available
                doc_meta = doc_metadata_map.get(filename, {})
                chunk_metadata = doc_meta.get("metadata", {})
                
                documents.append({
                    "filename": filename,
                    "file_path": str(file_path),
                    "file_size": stat.st_size,
                    "upload_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "file_type": file_path.suffix[1:] if file_path.suffix else "unknown",
                    # Include metadata from vector store chunks
                    "metadata": {
                        "project_id": chunk_metadata.get("project_id"),
                        "phase": chunk_metadata.get("phase"),
                        "purpose": chunk_metadata.get("purpose"),
                        "category": chunk_metadata.get("category"),
                        "uploaded_by": chunk_metadata.get("uploaded_by"),
                        "upload_timestamp": chunk_metadata.get("upload_timestamp"),
                        "original_filename": chunk_metadata.get("original_filename"),
                        "chunk_count": len(doc_meta.get("chunk_ids", [])),
                        "chunk_ids": doc_meta.get("chunk_ids", [])
                    }
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
