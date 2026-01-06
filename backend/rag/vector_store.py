"""
Vector Store: Manages embeddings and similarity search
Uses FAISS for efficient vector similarity search

Dependencies:
- anthropic: For generating embeddings via Claude (or use voyage-ai for dedicated embeddings)
- faiss-cpu or faiss-gpu: Vector similarity search
- numpy: Array operations
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Any
from pathlib import Path
from sentence_transformers import SentenceTransformer

try:
    import faiss
except ImportError:
    print("⚠️  Warning: FAISS not installed. Install with: pip install faiss-cpu")
    faiss = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class VectorStore:
    """
    Manages document embeddings and similarity search using FAISS
    
    Dependencies:
    - faiss-cpu: Efficient similarity search
    - sentence-transformers: For generating embeddings
    """
    
    def __init__(
        self,
        api_key: str = None,
        embedding_dimension: int = 384,  # all-MiniLM-L6-v2 dimension
        index_path: str = "data/vector_db/faiss_index",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize vector store
        
        Args:
            api_key: Optional API key (kept for compatibility)
            embedding_dimension: Dimension of embedding vectors (384 for MiniLM, 768 for mpnet)
            index_path: Path to save/load FAISS index
            embedding_model: Sentence-transformers model name
        """
        if not faiss:
            raise ImportError("faiss not installed. Install with: pip install faiss-cpu")
        
        # Initialize sentence-transformers model for embeddings
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dimension = embedding_dimension
        self.index_path = Path(index_path)
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(embedding_dimension)  # L2 distance
        self.chunks = []  # Store original chunks
        self.metadata = []  # Store metadata
        
        # Create directory if needed
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Embedding model loaded (dimension: {embedding_dimension})")
    
    def add_documents(self, chunks: List) -> None:
        """
        Add document chunks to vector store
        
        Args:
            chunks: List of DocumentChunk objects
        """
        print(f"Generating embeddings for {len(chunks)} chunks...")
        
        # Generate embeddings in batches
        batch_size = 10
        embeddings = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_embeddings = self._generate_embeddings([c.content for c in batch])
            embeddings.extend(batch_embeddings)
            
            print(f"  Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store chunks and metadata
        self.chunks.extend(chunks)
        self.metadata.extend([c.metadata for c in chunks])
        
        print(f"✅ Added {len(chunks)} chunks to vector store")
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using sentence-transformers
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        # Use sentence-transformers to generate embeddings
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return embeddings.tolist()
    
    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Optional threshold for similarity scores
            
        Returns:
            List of (chunk_dict, score) tuples
        """
        # Generate query embedding
        query_embedding = self._generate_embeddings([query])[0]
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS
        distances, indices = self.index.search(query_vector, k)
        
        # Prepare results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):  # Valid index
                score = float(distance)
                
                # Apply score threshold if provided
                if score_threshold is None or score <= score_threshold:
                    chunk = self.chunks[idx]
                    results.append((
                        {
                            'content': chunk.content,
                            'metadata': chunk.metadata,
                            'chunk_id': chunk.chunk_id,
                            'score': score
                        },
                        score
                    ))
        
        return results
    
    def save(self) -> None:
        """Save index and metadata to disk"""
        # Save FAISS index
        index_file = str(self.index_path) + '.faiss'
        faiss.write_index(self.index, index_file)
        
        # Save chunks and metadata
        data_file = str(self.index_path) + '.pkl'
        with open(data_file, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata
            }, f)
        
        print(f"✅ Vector store saved to {self.index_path}")
    
    def load(self) -> bool:
        """
        Load index and metadata from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        index_file = str(self.index_path) + '.faiss'
        data_file = str(self.index_path) + '.pkl'
        
        if not os.path.exists(index_file) or not os.path.exists(data_file):
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_file)
            
            # Load chunks and metadata
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']
            
            print(f"✅ Loaded vector store with {len(self.chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False

    def delete_by_source(self, source_filename: str) -> Dict:
        """
        Delete all chunks associated with a specific source document
        
        FAISS doesn't support direct deletion, so we need to:
        1. Filter out chunks from the document
        2. Rebuild the index with remaining chunks
        
        Args:
            source_filename: The filename/source identifier to delete
            
        Returns:
            Dict with deletion results (success, deleted_chunks count)
        """
        # Find indices of chunks to keep (those NOT from this source)
        chunks_to_keep = []
        metadata_to_keep = []
        deleted_count = 0
        
        for i, chunk in enumerate(self.chunks):
            # Check multiple metadata fields where the filename might be stored
            chunk_source = chunk.metadata.get('source', '')
            chunk_file_path = chunk.metadata.get('file_path', '')
            original_filename = chunk.metadata.get('original_filename', '')
            
            # Check if this chunk belongs to the document being deleted
            is_match = (
                source_filename in chunk_source or
                source_filename in chunk_file_path or
                source_filename == original_filename or
                chunk_source.endswith(source_filename) or
                chunk_file_path.endswith(source_filename)
            )
            
            if is_match:
                deleted_count += 1
            else:
                chunks_to_keep.append(chunk)
                metadata_to_keep.append(self.metadata[i])
        
        if deleted_count == 0:
            return {
                "success": False,
                "deleted_chunks": 0,
                "message": f"No chunks found for source: {source_filename}"
            }
        
        # Rebuild the index with remaining chunks
        print(f"Rebuilding index after deleting {deleted_count} chunks...")
        
        # Reset the index
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        
        if chunks_to_keep:
            # Re-generate embeddings and add to index
            batch_size = 10
            embeddings = []
            
            for i in range(0, len(chunks_to_keep), batch_size):
                batch = chunks_to_keep[i:i + batch_size]
                batch_embeddings = self._generate_embeddings([c.content for c in batch])
                embeddings.extend(batch_embeddings)
            
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
        
        # Update chunks and metadata
        self.chunks = chunks_to_keep
        self.metadata = metadata_to_keep
        
        print(f"✅ Deleted {deleted_count} chunks, {len(self.chunks)} remaining")
        
        return {
            "success": True,
            "deleted_chunks": deleted_count,
            "remaining_chunks": len(self.chunks)
        }


# Example usage
def main():
    """Test the vector store"""
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return
    
    # Create vector store
    store = VectorStore(api_key)
    
    # Try to load existing index
    if not store.load():
        print("No existing index found. Create one first using document_processor.py")
        return
    
    # Test search
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "market research requirements"
    
    print(f"\nSearching for: '{query}'")
    results = store.search(query, k=3)
    
    print(f"\nFound {len(results)} results:")
    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   Source: {chunk['metadata']['source']}")
        print(f"   Content: {chunk['content'][:200]}...")


if __name__ == "__main__":
    main()
