# Docling Integration Usage Guide

**Last Updated:** October 2025  
**Status:** Production Ready ✅

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Integration with RAG Pipeline](#integration-with-rag-pipeline)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

The Docling integration is **automatic and transparent**. Your existing code will now use enhanced document processing without any changes!

```python
# This now uses Docling under the hood!
from rag.docling_processor import DoclingProcessor as DocumentProcessor

processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
chunks = processor.process_document("document.pdf")
```

---

## Installation

### Basic Installation

Docling is included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install docling
```

### With OCR Support (Optional)

For scanned documents:

```bash
pip install docling[ocr]
```

### macOS-Specific

If you encounter PyArrow issues on macOS:

```bash
# Install PyArrow via conda first
conda install -c conda-forge pyarrow

# Then install Docling
pip install docling
```

---

## Basic Usage

### Process Single Document

```python
from rag.docling_processor import DoclingProcessor

# Initialize processor
processor = DoclingProcessor(
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200     # Overlap for context preservation
)

# Process any supported format
chunks = processor.process_document("document.pdf")

# View results
print(f"Extracted {len(chunks)} chunks")
for chunk in chunks[:3]:
    print(f"\nChunk ID: {chunk.chunk_id}")
    print(f"Type: {chunk.metadata.get('content_type')}")
    print(f"Content: {chunk.content[:100]}...")
```

### Process Directory

```python
from rag.docling_processor import DoclingProcessor

processor = DoclingProcessor()

# Process all supported documents in directory
chunks = processor.process_directory("data/documents/")

# Docling automatically handles:
# - PDFs (with layout understanding)
# - DOCX files
# - PPTX presentations
# - XLSX spreadsheets
# - HTML files
# - Images (PNG, JPG, TIFF, etc.)

print(f"Total chunks from all documents: {len(chunks)}")
```

### Command Line Usage

```bash
# Process single document
python rag/docling_processor.py path/to/document.pdf

# Process directory
python rag/docling_processor.py data/documents/

# View sample chunks
python rag/docling_processor.py document.pdf | head -50
```

---

## Advanced Features

For specialized use cases, use the advanced processor:

### Enable OCR for Scanned Documents

```python
from rag.docling_advanced import AdvancedDoclingProcessor

# Initialize with OCR enabled
processor = AdvancedDoclingProcessor(
    enable_ocr=True,
    enable_table_structure=True,
    enable_images=True
)

# Process scanned PDF
result = processor.process_with_ocr("scanned_rfp.pdf")

print(f"Pages processed: {result['ocr_stats']['pages_processed']}")
print(f"Text extracted: {len(result['text'])} characters")
```

### Extract Tables with Enhanced Structure

```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor(enable_table_structure=True)

# Extract all tables from document
tables = processor.extract_enhanced_tables("pricing_document.pdf")

for i, table in enumerate(tables, 1):
    print(f"\nTable {i}:")
    print(f"  Page: {table['page']}")
    print(f"  Caption: {table['caption']}")
    print(f"  Markdown:\n{table['markdown']}")
```

### Extract Images and Captions

```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor(enable_images=True)

# Extract all images
images = processor.extract_images("technical_spec.pdf")

for img in images:
    print(f"\nImage {img['index']}:")
    print(f"  Page: {img['page']}")
    print(f"  Caption: {img['caption']}")
```

### Export to Structured JSON

```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor()

# Export document to lossless JSON representation
json_data = processor.export_to_json(
    "document.pdf",
    output_path="document_structure.json"
)

# JSON contains:
# - Complete document structure
# - All text with formatting
# - Table structures
# - Image references
# - Metadata (title, authors, etc.)
```

### Get Document Metadata

```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor()

metadata = processor.get_document_metadata("document.pdf")

print(f"Title: {metadata.get('title', 'N/A')}")
print(f"Authors: {metadata.get('authors', 'N/A')}")
print(f"Pages: {metadata['page_count']}")
print(f"File size: {metadata['file_size']} bytes")
```

### Analyze Document Structure

```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor()

analysis = processor.analyze_document_structure("document.pdf")

print(f"Pages: {analysis['page_count']}")
print(f"Total elements: {analysis['total_elements']}")
print("\nContent breakdown:")
for content_type, count in analysis['content_types'].items():
    print(f"  {content_type}: {count}")
```

---

## Integration with RAG Pipeline

### Update Existing RAG Setup

No changes needed! The integration scripts already use Docling:

```bash
# Setup RAG system (now uses Docling automatically)
python scripts/setup_rag_system.py

# Add new documents (now with enhanced processing)
python scripts/add_documents_to_rag.py path/to/new_document.pdf
```

### Manual Integration

```python
from rag.docling_processor import DoclingProcessor
from rag.vector_store import VectorStore

# Initialize enhanced processor
processor = DoclingProcessor(chunk_size=1000, chunk_overlap=200)

# Process documents
chunks = processor.process_directory("data/documents/")

# Add to vector store (same as before)
vector_store = VectorStore(
    api_key=api_key,
    embedding_dimension=384,
    index_path="data/vector_db/faiss_index"
)

vector_store.add_documents(chunks)
vector_store.save()

print(f"✅ Added {len(chunks)} enhanced chunks to RAG system")
```

---

## Examples

### Example 1: Process Government RFP with Tables

```python
from rag.docling_processor import DoclingProcessor

processor = DoclingProcessor()

# Process RFP with complex tables and multi-column layout
chunks = processor.process_document("government_rfp.pdf")

# Docling automatically:
# ✅ Detects correct reading order in multi-column layout
# ✅ Extracts pricing tables with structure preserved
# ✅ Identifies sections and headers
# ✅ Separates tables as dedicated chunks for better retrieval

# Find table chunks
table_chunks = [c for c in chunks if c.metadata.get('content_type') == 'table']
print(f"Found {len(table_chunks)} pricing/data tables")
```

### Example 2: Process Mixed Document Types

```python
from rag.docling_processor import DoclingProcessor

processor = DoclingProcessor()

# Process various document formats
documents = [
    "technical_spec.pdf",        # PDF with diagrams
    "cost_estimate.xlsx",        # Excel spreadsheet
    "presentation.pptx",         # PowerPoint presentation
    "requirements.docx",         # Word document
    "vendor_info.html"           # HTML report
]

all_chunks = []
for doc in documents:
    chunks = processor.process_document(f"data/{doc}")
    all_chunks.extend(chunks)
    print(f"✓ {doc}: {len(chunks)} chunks")

print(f"\nTotal: {len(all_chunks)} chunks from {len(documents)} documents")
```

### Example 3: Process Scanned Legacy Documents

```python
from rag.docling_advanced import AdvancedDoclingProcessor

# Enable OCR for scanned documents
processor = AdvancedDoclingProcessor(enable_ocr=True)

# Process old scanned contract
result = processor.process_with_ocr("legacy_contract_scan.pdf")

# Check OCR quality
if result['ocr_stats']['has_ocr_text']:
    print("✅ Successfully extracted text from scanned document")
    print(f"   Extracted: {len(result['text'])} characters")
else:
    print("⚠️  OCR found no text - may be pure images")

# Save extracted text
with open("extracted_contract.txt", "w") as f:
    f.write(result['text'])
```

### Example 4: Extract All Tables from Financial Report

```python
from rag.docling_advanced import AdvancedDoclingProcessor
import pandas as pd

processor = AdvancedDoclingProcessor(enable_table_structure=True)

# Extract all tables
tables = processor.extract_enhanced_tables("financial_report.pdf")

print(f"Found {len(tables)} tables\n")

# Process each table
for i, table in enumerate(tables, 1):
    print(f"Table {i} (Page {table['page']}):")
    print(f"Caption: {table['caption']}")
    print("\nMarkdown representation:")
    print(table['markdown'][:200] + "...")
    
    # Could convert to DataFrame for analysis
    # if table has structured_data
    if 'structured_data' in table:
        # Process structured data
        pass
    
    print("\n" + "-"*70 + "\n")
```

### Example 5: Compare Old vs New Processor

```python
from rag.document_processor import DocumentProcessor as BasicProcessor
from rag.docling_processor import DoclingProcessor

# Process with both processors
basic = BasicProcessor()
docling = DoclingProcessor()

file_path = "complex_document.pdf"

print("Processing with basic processor...")
basic_chunks = basic.process_pdf(file_path)

print("Processing with Docling...")
docling_chunks = docling.process_document(file_path)

print("\nComparison:")
print(f"Basic processor:   {len(basic_chunks)} chunks")
print(f"Docling processor: {len(docling_chunks)} chunks")

# Check for table chunks (only Docling extracts these)
docling_tables = [c for c in docling_chunks if c.metadata.get('content_type') == 'table']
print(f"Tables extracted:  {len(docling_tables)} (Docling only)")
```

---

## Troubleshooting

### Issue: "Docling not installed"

**Solution:**
```bash
pip install docling
```

If on macOS with PyArrow issues:
```bash
conda install -c conda-forge pyarrow
pip install docling
```

### Issue: "Processing very slow on first run"

**Explanation:** Docling downloads ML models (~100-500MB) on first use.

**Solution:** Wait for models to download. Subsequent runs will be fast.

```python
# Check if models are being downloaded
# You'll see progress bars on first run
```

### Issue: "OCR not working"

**Solution:** Install OCR dependencies:
```bash
pip install docling[ocr]
```

### Issue: "Table extraction returns empty"

**Possible causes:**
1. Document has no tables
2. Tables are actually images (enable OCR)
3. Table structure is too complex

**Debug:**
```python
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor(enable_table_structure=True)

# Analyze document structure first
analysis = processor.analyze_document_structure("document.pdf")
print(f"Has tables: {analysis['has_tables']}")
print(f"Content types: {analysis['content_types']}")
```

### Issue: "Fallback to basic processor"

**Explanation:** Docling encountered an error and used the basic processor.

**Debug:**
```python
# Check error message in console
# Common causes:
# - Corrupted PDF
# - Unsupported encryption
# - Very large file

# Try basic processor directly
from rag.document_processor import DocumentProcessor
basic = DocumentProcessor()
chunks = basic.process_pdf("problematic.pdf")
```

### Issue: "Chunks seem lower quality than expected"

**Check:**
```python
# Verify Docling is being used
for chunk in chunks[:5]:
    processor_used = chunk.metadata.get('processor', 'unknown')
    print(f"Chunk processed by: {processor_used}")
    # Should show 'docling', not missing
```

### Issue: "Memory error on large documents"

**Solution:** Process in smaller batches or increase system memory.

```python
# Process pages in batches
# (Not directly supported, but can split PDF first)

# Or increase chunk size to reduce number of chunks
processor = DoclingProcessor(
    chunk_size=2000,  # Larger chunks
    chunk_overlap=200
)
```

---

## Performance Tips

### Batch Processing

```python
from pathlib import Path
from rag.docling_processor import DoclingProcessor

processor = DoclingProcessor()

# Process multiple documents efficiently
documents = Path("data/documents").glob("*.pdf")

for doc in documents:
    try:
        chunks = processor.process_document(str(doc))
        print(f"✓ {doc.name}: {len(chunks)} chunks")
    except Exception as e:
        print(f"✗ {doc.name}: {e}")
```

### Reuse Processor Instance

```python
# ✅ GOOD: Reuse processor (models loaded once)
processor = DoclingProcessor()
for doc in documents:
    chunks = processor.process_document(doc)

# ❌ BAD: Create new processor each time (reloads models)
for doc in documents:
    processor = DoclingProcessor()  # Wasteful!
    chunks = processor.process_document(doc)
```

### Adjust Chunk Size for Your Use Case

```python
# For detailed extraction (more chunks)
processor = DoclingProcessor(chunk_size=500, chunk_overlap=100)

# For broader context (fewer chunks)
processor = DoclingProcessor(chunk_size=2000, chunk_overlap=300)

# Default (balanced)
processor = DoclingProcessor(chunk_size=1000, chunk_overlap=200)
```

---

## Best Practices

### 1. Use Docling for New Ingestion

```python
# ✅ For new documents, use Docling
from rag.docling_processor import DoclingProcessor as DocumentProcessor
```

### 2. Keep Basic Processor as Fallback

The system automatically falls back to basic processing if Docling fails - no action needed!

### 3. Enable OCR Only When Needed

OCR is slower - only enable for scanned documents:

```python
# Check if document needs OCR first
# If digital PDF, don't use OCR
processor = DoclingProcessor()  # Faster

# Only if scanned
from rag.docling_advanced import AdvancedDoclingProcessor
processor = AdvancedDoclingProcessor(enable_ocr=True)
```

### 4. Extract Tables Separately for Critical Data

```python
# For documents with important tables (pricing, specs)
from rag.docling_advanced import AdvancedDoclingProcessor

processor = AdvancedDoclingProcessor(enable_table_structure=True)
tables = processor.extract_enhanced_tables("pricing_doc.pdf")

# Process tables separately or with special handling
```

### 5. Monitor Chunk Quality

```python
# Check metadata to verify Docling is being used
sample_chunks = chunks[:10]
for chunk in sample_chunks:
    print(f"Processor: {chunk.metadata.get('processor')}")
    print(f"Type: {chunk.metadata.get('content_type')}")
```

---

## Additional Resources

- **Docling GitHub:** https://github.com/docling-project/docling
- **Docling Documentation:** https://docling-project.github.io/docling
- **Technical Report:** https://arxiv.org/abs/2408.09869
- **RAG Enhancement README:** `RAG_ENHANCEMENT_README.md`
- **Integration Plan:** `docling-integration-plan.plan.md`

---

## Support

### Questions?

- **Installation issues:** See [Installation](#installation) section
- **Processing errors:** See [Troubleshooting](#troubleshooting) section
- **Advanced features:** See [Advanced Features](#advanced-features) section

### Reporting Issues

Include:
1. Error message
2. Document type/format
3. Python version and OS
4. Whether basic processor works for same document

---

**Last Updated:** October 2025  
**Status:** Production Ready ✅  
**Integration:** Automatic and Transparent  
**Backward Compatible:** Yes ✅

