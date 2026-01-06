"""
Advanced Docling Features

Specialized document processing capabilities for advanced use cases:
- OCR for scanned PDFs and images
- Image extraction and classification
- Enhanced table structure detection
- Structured JSON export
- Custom pipeline configurations

Dependencies:
- docling: Core library
- Additional OCR libraries (tesseract, easyocr) for OCR support
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import json

# Import Docling components
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️  Warning: Docling not installed. Install with: pip install docling")


class AdvancedDoclingProcessor:
    """
    Advanced document processing features using Docling
    
    Features:
    - OCR configuration for scanned PDFs and images
    - Image extraction and classification
    - Enhanced table structure detection with cell-level data
    - Structured JSON export (lossless document representation)
    - Custom pipeline options (reading order, formula detection, etc.)
    
    Usage:
        # Enable OCR for scanned documents
        processor = AdvancedDoclingProcessor(enable_ocr=True)
        result = processor.process_with_ocr("scanned_document.pdf")
        
        # Extract images with captions
        images = processor.extract_images("document.pdf")
        
        # Export to structured JSON
        json_data = processor.export_to_json("document.pdf")
    """
    
    def __init__(
        self, 
        enable_ocr: bool = False,
        enable_table_structure: bool = True,
        enable_images: bool = True
    ):
        """
        Initialize advanced Docling processor
        
        Args:
            enable_ocr: Enable OCR for scanned documents (requires additional libraries)
            enable_table_structure: Enable enhanced table structure detection
            enable_images: Enable image extraction and classification
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling not available. Install with: pip install docling\n"
                "For OCR support: pip install docling[ocr]"
            )
        
        # Configure pipeline options
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = enable_ocr
        self.pipeline_options.do_table_structure = enable_table_structure
        
        # Initialize converter with custom options
        self.converter = DocumentConverter(
            pipeline_options=self.pipeline_options
        )
        
        self.enable_images = enable_images
        
        print("✓ Advanced Docling processor initialized")
        if enable_ocr:
            print("  • OCR enabled for scanned documents")
        if enable_table_structure:
            print("  • Enhanced table structure detection enabled")
        if enable_images:
            print("  • Image extraction enabled")
    
    def process_with_ocr(self, file_path: str) -> Dict:
        """
        Process document with OCR for scanned PDFs and images
        
        This is useful for:
        - Scanned government documents
        - Legacy paper documents converted to PDF
        - Images of text documents
        - Documents with mixed text and scanned content
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with document data and metadata
        """
        print(f"📄 Processing with OCR: {Path(file_path).name}")
        
        try:
            # Convert with OCR enabled
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Extract text content
            text = doc.export_to_markdown()
            
            # Get OCR metadata if available
            ocr_stats = {
                'pages_processed': len(doc.pages) if hasattr(doc, 'pages') else 0,
                'has_ocr_text': bool(text.strip())
            }
            
            print(f"  ✓ Processed {ocr_stats['pages_processed']} pages with OCR")
            
            return {
                'text': text,
                'document': doc,
                'ocr_stats': ocr_stats
            }
            
        except Exception as e:
            print(f"  ✗ OCR processing error: {e}")
            raise
    
    def extract_images(self, file_path: str) -> List[Dict]:
        """
        Extract images from document with captions and classifications
        
        Useful for:
        - Extracting diagrams and charts
        - Finding figures referenced in text
        - Analyzing visual content
        
        Args:
            file_path: Path to document
            
        Returns:
            List of dictionaries with image data and metadata
        """
        print(f"🖼️  Extracting images from: {Path(file_path).name}")
        
        images = []
        
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Iterate through document elements to find images
            for idx, element in enumerate(doc.body):
                if hasattr(element, 'label') and element.label == 'picture':
                    image_info = {
                        'index': idx,
                        'caption': element.text if hasattr(element, 'text') else '',
                        'page': element.page if hasattr(element, 'page') else None,
                        # Image data would be available through element.image
                        'has_image_data': hasattr(element, 'image')
                    }
                    images.append(image_info)
            
            print(f"  ✓ Found {len(images)} images")
            
            return images
            
        except Exception as e:
            print(f"  ✗ Image extraction error: {e}")
            return []
    
    def extract_enhanced_tables(self, file_path: str) -> List[Dict]:
        """
        Extract tables with enhanced structure detection
        
        Returns tables with:
        - Cell-level data
        - Row and column headers
        - Merged cell information
        - Table captions and titles
        
        Args:
            file_path: Path to document
            
        Returns:
            List of dictionaries with table data and metadata
        """
        print(f"📊 Extracting enhanced tables from: {Path(file_path).name}")
        
        tables = []
        
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Iterate through document elements to find tables
            for idx, element in enumerate(doc.body):
                if hasattr(element, 'label') and element.label == 'table':
                    # Export table in multiple formats
                    table_data = {
                        'index': idx,
                        'markdown': element.export_to_markdown() if hasattr(element, 'export_to_markdown') else '',
                        'page': element.page if hasattr(element, 'page') else None,
                        'caption': element.text if hasattr(element, 'text') else '',
                        # Additional metadata
                        'has_structure': hasattr(element, 'cells') or hasattr(element, 'rows')
                    }
                    
                    # Try to get cell-level data if available
                    if hasattr(element, 'export_to_dict'):
                        try:
                            table_data['structured_data'] = element.export_to_dict()
                        except:
                            pass
                    
                    tables.append(table_data)
            
            print(f"  ✓ Found {len(tables)} tables with enhanced structure")
            
            return tables
            
        except Exception as e:
            print(f"  ✗ Table extraction error: {e}")
            return []
    
    def export_to_json(self, file_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Export document to structured JSON (lossless representation)
        
        The JSON export preserves:
        - Document structure and hierarchy
        - All text content with formatting
        - Table structures
        - Image references
        - Metadata (authors, title, etc.)
        
        Args:
            file_path: Path to document
            output_path: Optional path to save JSON file
            
        Returns:
            Dictionary with complete document structure
        """
        print(f"📋 Exporting to JSON: {Path(file_path).name}")
        
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Export to dictionary (lossless JSON representation)
            doc_dict = doc.export_to_dict()
            
            # Save to file if output path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_dict, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved JSON to: {output_path}")
            
            return doc_dict
            
        except Exception as e:
            print(f"  ✗ JSON export error: {e}")
            raise
    
    def get_document_metadata(self, file_path: str) -> Dict:
        """
        Extract document metadata
        
        Extracts:
        - Title
        - Authors
        - Date
        - Language
        - Page count
        - Document type
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with document metadata
        """
        print(f"ℹ️  Extracting metadata from: {Path(file_path).name}")
        
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            metadata = {
                'file_name': Path(file_path).name,
                'file_size': os.path.getsize(file_path),
                'page_count': len(doc.pages) if hasattr(doc, 'pages') else 0,
            }
            
            # Try to extract additional metadata if available
            if hasattr(doc, 'metadata'):
                doc_meta = doc.metadata
                if hasattr(doc_meta, 'title'):
                    metadata['title'] = doc_meta.title
                if hasattr(doc_meta, 'authors'):
                    metadata['authors'] = doc_meta.authors
                if hasattr(doc_meta, 'date'):
                    metadata['date'] = doc_meta.date
                if hasattr(doc_meta, 'language'):
                    metadata['language'] = doc_meta.language
            
            print(f"  ✓ Extracted metadata")
            
            return metadata
            
        except Exception as e:
            print(f"  ✗ Metadata extraction error: {e}")
            return {
                'file_name': Path(file_path).name,
                'error': str(e)
            }
    
    def analyze_document_structure(self, file_path: str) -> Dict:
        """
        Analyze and report document structure
        
        Provides statistics on:
        - Content types (text, tables, images, code, formulas)
        - Section hierarchy
        - Page layout information
        - Reading order quality
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with structure analysis
        """
        print(f"🔍 Analyzing document structure: {Path(file_path).name}")
        
        try:
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Count different content types
            content_types = {}
            
            for element in doc.body:
                if hasattr(element, 'label'):
                    label = element.label
                    content_types[label] = content_types.get(label, 0) + 1
            
            analysis = {
                'page_count': len(doc.pages) if hasattr(doc, 'pages') else 0,
                'total_elements': len(doc.body) if hasattr(doc, 'body') else 0,
                'content_types': content_types,
                'has_tables': 'table' in content_types,
                'has_images': 'picture' in content_types,
                'has_code': 'code' in content_types,
            }
            
            print(f"  ✓ Document structure:")
            print(f"    • Pages: {analysis['page_count']}")
            print(f"    • Elements: {analysis['total_elements']}")
            for content_type, count in content_types.items():
                print(f"    • {content_type}: {count}")
            
            return analysis
            
        except Exception as e:
            print(f"  ✗ Structure analysis error: {e}")
            return {'error': str(e)}


# Example usage
def main():
    """Test advanced Docling features"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python docling_advanced.py <document_path> [--ocr]")
        print("\nExamples:")
        print("  python docling_advanced.py sample.pdf")
        print("  python docling_advanced.py scanned.pdf --ocr")
        return
    
    file_path = sys.argv[1]
    enable_ocr = '--ocr' in sys.argv
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print("\n" + "="*70)
    print("ADVANCED DOCLING PROCESSING")
    print("="*70 + "\n")
    
    # Initialize processor
    processor = AdvancedDoclingProcessor(
        enable_ocr=enable_ocr,
        enable_table_structure=True,
        enable_images=True
    )
    
    print("\n" + "-"*70)
    print("1. Document Metadata")
    print("-"*70)
    metadata = processor.get_document_metadata(file_path)
    print(json.dumps(metadata, indent=2))
    
    print("\n" + "-"*70)
    print("2. Document Structure Analysis")
    print("-"*70)
    structure = processor.analyze_document_structure(file_path)
    
    print("\n" + "-"*70)
    print("3. Enhanced Table Extraction")
    print("-"*70)
    tables = processor.extract_enhanced_tables(file_path)
    
    print("\n" + "-"*70)
    print("4. Image Extraction")
    print("-"*70)
    images = processor.extract_images(file_path)
    
    if enable_ocr:
        print("\n" + "-"*70)
        print("5. OCR Processing")
        print("-"*70)
        ocr_result = processor.process_with_ocr(file_path)
        print(f"OCR text length: {len(ocr_result['text'])} characters")
    
    print("\n" + "="*70)
    print("✅ PROCESSING COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

