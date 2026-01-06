"""
Table-Aware Retriever: Enhanced retrieval for tabular data
Handles queries that reference specific columns, rows, or data points
"""

from typing import List, Dict
from .retriever import Retriever
import re


class TableAwareRetriever:
    """
    Enhanced retriever for tabular data in RAG systems
    
    Features:
    - Detects table-related queries
    - Enhances queries with column names
    - Filters results by table metadata
    - Formats tabular results for better LLM consumption
    
    Dependencies:
    - Retriever: Base RAG retriever
    """
    
    def __init__(self, base_retriever: Retriever):
        """
        Initialize table-aware retriever
        
        Args:
            base_retriever: Base Retriever instance
        """
        self.retriever = base_retriever
    
    def retrieve_table_data(
        self,
        query: str,
        table_name: str = None,
        column_filter: List[str] = None,
        k: int = 5
    ) -> List[Dict]:
        """
        Retrieve data from tabular sources
        
        Args:
            query: Search query
            table_name: Optional table/sheet name filter
            column_filter: Optional list of column names to focus on
            k: Number of results to return
            
        Returns:
            List of retrieved documents with table context
        """
        # Enhance query for table data
        enhanced_query = self._enhance_table_query(query, table_name, column_filter)
        
        # Retrieve documents
        documents = self.retriever.retrieve(enhanced_query, k=k * 2)  # Get more, then filter
        
        # Filter for table documents if requested
        if table_name or column_filter:
            documents = self._filter_table_documents(documents, table_name, column_filter)
        
        # Take top k
        documents = documents[:k]
        
        # Enhance metadata for better LLM context
        for doc in documents:
            doc = self._enhance_table_metadata(doc)
        
        return documents
    
    def _enhance_table_query(
        self,
        query: str,
        table_name: str = None,
        column_filter: List[str] = None
    ) -> str:
        """Enhance query with table-specific context"""
        enhanced = query
        
        if table_name:
            enhanced = f"{table_name} table: {enhanced}"
        
        if column_filter:
            columns_str = ", ".join(column_filter)
            enhanced = f"{enhanced} columns: {columns_str}"
        
        # Add table-related keywords
        if any(word in query.lower() for word in ['data', 'value', 'number', 'count']):
            enhanced = f"tabular data {enhanced}"
        
        return enhanced
    
    def _filter_table_documents(
        self,
        documents: List[Dict],
        table_name: str = None,
        column_filter: List[str] = None
    ) -> List[Dict]:
        """Filter documents based on table criteria"""
        filtered = []
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            
            # Check file type
            if metadata.get('file_type') not in ['excel', 'csv']:
                continue
            
            # Check table name
            if table_name and metadata.get('sheet_name', '').lower() != table_name.lower():
                continue
            
            # Check columns
            if column_filter:
                doc_columns = metadata.get('columns', '').lower()
                if not any(col.lower() in doc_columns for col in column_filter):
                    continue
            
            filtered.append(doc)
        
        return filtered
    
    def _enhance_table_metadata(self, doc: Dict) -> Dict:
        """Add helpful table context to document"""
        metadata = doc.get('metadata', {})
        
        if metadata.get('file_type') in ['excel', 'csv']:
            # Add table context to content
            table_context = []
            
            if 'sheet_name' in metadata:
                table_context.append(f"[Table: {metadata['sheet_name']}]")
            
            if 'columns' in metadata:
                table_context.append(f"[Columns: {metadata['columns']}]")
            
            if 'row_start' in metadata and 'row_end' in metadata:
                table_context.append(f"[Rows: {metadata['row_start']}-{metadata['row_end']}]")
            
            if table_context:
                context_str = " ".join(table_context)
                doc['content'] = f"{context_str}\n\n{doc['content']}"
        
        return doc
    
    def retrieve_specific_columns(
        self,
        query: str,
        columns: List[str],
        k: int = 5
    ) -> List[Dict]:
        """
        Retrieve data focusing on specific columns
        
        Args:
            query: Search query
            columns: Column names to focus on
            k: Number of results
            
        Returns:
            Retrieved documents filtered by columns
        """
        return self.retrieve_table_data(
            query=query,
            column_filter=columns,
            k=k
        )
