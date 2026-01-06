"""
Retriever: High-level interface for RAG queries
Combines vector search with re-ranking and context assembly
"""

import os
import sys
from typing import List, Dict

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Try relative import first, fall back to absolute
try:
    from .vector_store import VectorStore
except ImportError:
    from rag.vector_store import VectorStore


class Retriever:
    """
    High-level retrieval interface for RAG system
    
    Handles:
    - Query processing
    - Context retrieval
    - Re-ranking (optional)
    - Context assembly for LLM
    """
    
    def __init__(self, vector_store: VectorStore, top_k: int = 5):
        """
        Initialize retriever
        
        Args:
            vector_store: VectorStore instance
            top_k: Number of documents to retrieve
        """
        self.vector_store = vector_store
        self.top_k = top_k
    
    def retrieve(self, query: str, k: int = None) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            k: Number of results (overrides default top_k)
            
        Returns:
            List of retrieved document dictionaries
        """
        k = k or self.top_k
        
        # Search vector store
        results = self.vector_store.search(query, k=k)
        
        # Extract document dictionaries
        documents = [chunk for chunk, score in results]
        
        return documents
    
    def retrieve_with_context(self, query: str, k: int = None) -> str:
        """
        Retrieve and format documents as context string for LLM
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            Formatted context string
        """
        documents = self.retrieve(query, k=k)
        
        if not documents:
            return "No relevant information found in knowledge base."
        
        # Format as context
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc['metadata'].get('source', 'Unknown')
            content = doc['content']
            
            context_parts.append(
                f"[Source {i}: {source}]\n{content}\n"
            )
        
        context = "\n---\n\n".join(context_parts)
        
        return context
    
    def retrieve_for_section(
        self,
        section_name: str,
        section_guidance: str,
        project_info: Dict,
        k: int = None
    ) -> str:
        """
        Retrieve relevant context for a specific report section
        
        Args:
            section_name: Name of the section
            section_guidance: Guidance text for the section
            project_info: Project information dictionary
            k: Number of results
            
        Returns:
            Formatted context string
        """
        # Build enhanced query combining section info and project context
        query_parts = [
            section_name,
            section_guidance[:200],  # First 200 chars of guidance
        ]
        
        # Add relevant project info
        if 'product_service' in project_info:
            query_parts.append(project_info['product_service'])
        
        if 'critical_requirements' in project_info:
            query_parts.append(project_info['critical_requirements'])
        
        query = " ".join(query_parts)
        
        return self.retrieve_with_context(query, k=k)


# Example usage
def main():
    """Test the retriever"""
    from dotenv import load_dotenv
    from rag.vector_store import VectorStore
    
    load_dotenv()
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        return
    
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "small business opportunities in government contracting"
    
    print(f"\nQuery: '{query}'\n")
    
    # Initialize vector store and retriever
    print("Loading vector store...")
    vector_store = VectorStore(api_key)
    
    if not vector_store.load():
        print("❌ No vector store found. Run setup_rag_system.py first.")
        return
    
    print(f"✓ Loaded {len(vector_store.chunks)} chunks\n")
    
    retriever = Retriever(vector_store, top_k=5)
    
    # Retrieve documents
    documents = retriever.retrieve(query, k=5)
    
    if not documents:
        print("No relevant documents found.")
        return
    
    print(f"Found {len(documents)} results:")
    print("="*70)
    
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. Source: {doc['metadata']['source']}")
        print(f"   Score: {doc.get('score', 'N/A'):.4f}")
        print(f"   Preview: {doc['content'][:200]}...")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
