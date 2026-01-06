"""
Enhanced Document Processor using Docling

Replaces basic PyPDF2/python-docx processing with advanced parsing
that preserves layout, structure, and provides superior table extraction.

Key Features:
- Advanced PDF layout understanding (sections, headers, reading order)
- Structured table extraction with preserved formatting
- Multi-format support: PDF, DOCX, PPTX, XLSX, HTML, images
- OCR support for scanned documents
- Markdown export with preserved document structure

Dependencies:
- docling: Advanced document parsing and understanding
"""

import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

# Import Docling components
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️  Warning: Docling not installed. Install with: pip install docling")


@dataclass
class DocumentChunk:
    """
    Represents a chunk of text from a document
    
    Maintains compatibility with existing RAG pipeline
    """
    content: str
    metadata: Dict[str, str]
    chunk_id: str


class DoclingProcessor:
    """
    Advanced document processor using Docling
    
    Features:
    - Advanced PDF layout understanding with reading order detection
    - Superior table extraction maintaining structure
    - Multi-format support (PDF, DOCX, PPTX, XLSX, HTML, images)
    - Better text extraction quality than basic libraries
    - Metadata extraction from document structure
    
    Dependencies:
    - docling: Advanced document parsing (pip install docling)
    
    Usage:
        processor = DoclingProcessor(chunk_size=1000, chunk_overlap=200)
        chunks = processor.process_document("path/to/document.pdf")
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize Docling processor
        
        Args:
            chunk_size: Target size for text chunks (characters)
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize Docling converter once for efficiency
        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
        else:
            self.converter = None
            print("⚠️  Docling not available - will use fallback processor")
    
    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Process any supported document format using Docling
        
        Supported formats: PDF, DOCX, PPTX, XLSX, HTML, images, and more
        
        Args:
            file_path: Path to document
            
        Returns:
            List of DocumentChunk objects with enhanced metadata
        """
        file_name = Path(file_path).name
        print(f"  📄 Processing with Docling: {file_name}")
        
        # Check if Docling is available
        if not DOCLING_AVAILABLE or self.converter is None:
            print(f"    ⚠️  Docling not available, using fallback processor")
            return self._fallback_process(file_path)
        
        try:
            # Convert document - Docling handles format detection automatically
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Extract markdown (preserves structure better than plain text)
            # Markdown maintains headers, lists, tables, and formatting
            markdown_text = doc.export_to_markdown()
            
            # Extract tables separately for better chunking and retrieval
            tables = self._extract_tables(doc)
            
            # Create chunks from markdown with table handling
            chunks = self._create_chunks(
                text=markdown_text,
                file_path=file_path,
                tables=tables
            )
            
            print(f"    ✓ Extracted {len(chunks)} chunks ({len(tables)} tables)")
            return chunks
            
        except Exception as e:
            print(f"    ⚠️  Error processing with Docling: {e}")
            print(f"    → Falling back to basic processing")
            # Fallback to basic processing if Docling fails
            return self._fallback_process(file_path)
    
    def process_directory(self, directory_path: str) -> List[DocumentChunk]:
        """
        Process all documents in a directory
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            All chunks from all processed documents
        """
        chunks = []
        directory = Path(directory_path)
        
        print(f"🔍 Scanning directory: {directory_path}")
        
        # Supported formats by Docling
        supported_extensions = {
            '.pdf', '.docx', '.pptx', '.xlsx', 
            '.html', '.htm', '.txt', '.md',
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp'
        }
        
        # Find all supported files recursively
        files = [
            f for f in directory.rglob('*') 
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        print(f"📚 Found {len(files)} supported documents")
        print()
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}]", end=" ")
            file_chunks = self.process_document(str(file_path))
            chunks.extend(file_chunks)
        
        print()
        print(f"✅ Total chunks extracted: {len(chunks)}")
        return chunks
    
    def _extract_tables(self, doc) -> List[str]:
        """
        Extract tables with structure preserved
        
        Docling provides superior table extraction compared to basic libraries.
        Tables are converted to markdown format to preserve structure.
        
        Args:
            doc: Docling document object
            
        Returns:
            List of table markdown strings
        """
        tables = []
        
        try:
            # Iterate through document elements to find tables
            for element in doc.body:
                # Check if element is a table
                if hasattr(element, 'label') and element.label == 'table':
                    # Export table as markdown to preserve structure
                    table_md = element.export_to_markdown()
                    if table_md and table_md.strip():
                        tables.append(table_md)
        except Exception as e:
            print(f"      Note: Table extraction warning: {e}")
        
        return tables
    
    def _create_chunks(
        self, 
        text: str, 
        file_path: str, 
        tables: List[str]
    ) -> List[DocumentChunk]:
        """
        Create overlapping chunks from text with smart sentence-based splitting
        
        Strategy:
        - Split by sentences for better semantic boundaries
        - Maintain chunk_size and chunk_overlap for consistency
        - Store tables as separate chunks with special metadata
        - Add processor metadata for tracking
        
        Args:
            text: Full document text (markdown format)
            file_path: Source file path
            tables: Extracted tables as markdown
            
        Returns:
            List of document chunks with metadata
        """
        chunks = []
        file_name = Path(file_path).name
        file_type = Path(file_path).suffix[1:].lower()
        
        # Split text into sentences for better chunking
        # This preserves semantic units better than character splitting
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        chunk_count = 0
        
        # Build chunks by adding sentences
        for sentence in sentences:
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                # Save current chunk if it has content
                if current_chunk.strip():
                    chunk_count += 1
                    chunks.append(DocumentChunk(
                        content=current_chunk.strip(),
                        metadata={
                            'source': file_name,
                            'file_path': file_path,
                            'chunk_index': str(chunk_count),
                            'file_type': file_type,
                            'content_type': 'text',
                            'processor': 'docling'  # Track which processor was used
                        },
                        chunk_id=f"{file_name}_docling_chunk_{chunk_count}"
                    ))
                
                # Start new chunk with overlap
                # Take last N characters for overlap to maintain context
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + sentence + " "
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk_count += 1
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                metadata={
                    'source': file_name,
                    'file_path': file_path,
                    'chunk_index': str(chunk_count),
                    'file_type': file_type,
                    'content_type': 'text',
                    'processor': 'docling'
                },
                chunk_id=f"{file_name}_docling_chunk_{chunk_count}"
            ))
        
        # Add tables as separate chunks for better retrieval
        # Tables often contain critical data (pricing, specifications, etc.)
        for i, table in enumerate(tables, 1):
            chunk_count += 1
            chunks.append(DocumentChunk(
                content=f"Table {i}:\n\n{table}",
                metadata={
                    'source': file_name,
                    'file_path': file_path,
                    'chunk_index': str(chunk_count),
                    'file_type': file_type,
                    'content_type': 'table',  # Mark as table for specialized retrieval
                    'table_number': str(i),
                    'processor': 'docling'
                },
                chunk_id=f"{file_name}_docling_table_{i}"
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using common sentence boundaries
        
        This is better than character-based splitting as it preserves
        semantic units and context.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Split on common sentence endings
        # Handle common abbreviations and edge cases
        import re
        
        # Replace newlines with spaces, but preserve paragraph breaks
        text = re.sub(r'\n\n+', ' [PARAGRAPH] ', text)
        text = re.sub(r'\n', ' ', text)
        
        # Split on sentence boundaries
        # Look for period, exclamation, or question mark followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        # Restore paragraph breaks
        sentences = [s.replace('[PARAGRAPH]', '\n\n') for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _fallback_process(self, file_path: str) -> List[DocumentChunk]:
        """
        Fallback to basic processing if Docling fails or is unavailable
        
        Uses the existing basic document processor as a safety net.
        
        Args:
            file_path: Path to file
            
        Returns:
            Basic chunks using simple text extraction
        """
        # Import the basic processor
        try:
            from rag.document_processor import DocumentProcessor as BasicProcessor
            
            basic = BasicProcessor(self.chunk_size, self.chunk_overlap)
            
            # Route to appropriate basic method based on file type
            suffix = Path(file_path).suffix.lower()
            
            if suffix == '.pdf':
                return basic.process_pdf(file_path)
            elif suffix in ['.txt', '.md']:
                return basic.process_text_file(file_path)
            elif suffix == '.docx':
                return basic.process_docx(file_path)
            elif suffix in ['.xlsx', '.xls']:
                return basic.process_excel(file_path)
            elif suffix == '.csv':
                return basic.process_csv(file_path)
            else:
                print(f"      ✗ Unsupported file type: {suffix}")
                return []
                
        except Exception as e:
            print(f"      ✗ Fallback processing also failed: {e}")
            return []


# Example usage and testing
def main():
    """Test the Docling processor"""
    import sys
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = 'data/documents'
    
    # Initialize processor
    processor = DoclingProcessor(chunk_size=1000, chunk_overlap=200)
    
    # Check if target is file or directory
    target_path = Path(target)
    
    if target_path.is_file():
        # Process single file
        print(f"Processing single file: {target}")
        chunks = processor.process_document(str(target_path))
    elif target_path.is_dir():
        # Process directory
        print(f"Processing directory: {target}")
        chunks = processor.process_directory(target)
    else:
        print(f"❌ Path not found: {target}")
        return
    
    # Display results
    print(f"\n✅ Total chunks created: {len(chunks)}")
    
    # Show sample chunks
    if chunks:
        print("\nSample chunks:")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n{i}. ID: {chunk.chunk_id}")
            print(f"   Source: {chunk.metadata['source']}")
            print(f"   Type: {chunk.metadata.get('content_type', 'unknown')}")
            print(f"   Content preview: {chunk.content[:150]}...")


if __name__ == "__main__":
    main()

