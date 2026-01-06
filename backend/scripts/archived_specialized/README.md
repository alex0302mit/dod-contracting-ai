# Archived Specialized Scripts

**Purpose:** Specialized test scripts for specific features or formats.

**Status:** 🔧 Functional but rarely needed - kept for specific use cases

---

## Scripts in This Directory

### `test_web_search.py`
- **Purpose:** Test Tavily web search integration
- **Status:** ✅ Functional
- **When to Use:** Testing Tavily API configuration
- **Use Case:** 
  - Verifying TAVILY_API_KEY is set correctly
  - Testing market research web search functionality
  - Debugging search result quality
- **Alternative:** Web search is built into market research agents

### `test_xlsx_processing.py`
- **Purpose:** Test Excel file processing with RAG
- **Status:** ✅ Functional
- **When to Use:** Testing Excel document ingestion
- **Use Case:**
  - Verifying Excel files are processed correctly
  - Testing table extraction from spreadsheets
  - Debugging XLSX RAG integration
- **Alternative:** Excel processing built into `setup_rag_system.py`

### `generate_sf33.py`
- **Purpose:** Generate SF33 Solicitation form
- **Status:** ✅ Functional
- **When to Use:** Testing SF33 form generation specifically
- **Use Case:**
  - Testing SF33 agent independently
  - Debugging SF33 template issues
  - Generating just SF33 without full package
- **Alternative:** SF33 included in `test_full_pipeline.py`

---

## Should You Use These?

**Generally: No** - Their functionality is built into other scripts.

**When You Should Use Them:**

### Use `test_web_search.py` if:
- ❌ Web search not working in agents
- ❌ Need to verify Tavily API key
- ❌ Testing new search queries

### Use `test_xlsx_processing.py` if:
- ❌ Excel files not being processed by RAG
- ❌ Table extraction from Excel seems wrong
- ❌ Need to test XLSX-specific processing

### Use `generate_sf33.py` if:
- ❌ SF33 agent has issues
- ❌ Need only SF33 form (not full package)
- ❌ Testing SF33 template changes

---

## Related Current Scripts

**For normal use:**

### Web Search
- Use agents directly (search integrated)
- `generate_market_research_report.py` agent uses web search automatically

### Excel Processing
- `setup_rag_system.py` - Processes all formats including Excel
- `add_documents_to_rag.py` - Adds Excel files to RAG
- `test_docling_integration.py` - Tests all format processing

### SF33 Generation
- `test_full_pipeline.py` - Generates SF33 as part of complete package
- `generate_phase2_solicitation.py` - Includes SF33 in Phase 2

---

## Usage Examples

### Test Web Search
```bash
export TAVILY_API_KEY='your-key'
python scripts/archived_specialized/test_web_search.py
```

### Test Excel Processing
```bash
python scripts/archived_specialized/test_xlsx_processing.py path/to/file.xlsx
```

### Generate SF33 Only
```bash
python scripts/archived_specialized/generate_sf33.py
```

---

## Why These Are Archived

**Reason:** Specialized/specific functionality that most users don't need.

**What makes them "specialized":**
- Test one specific feature in isolation
- Used for debugging specific issues
- Functionality now integrated into broader scripts
- Rarely needed in normal workflow

**Keep them because:**
- Useful for debugging specific issues
- Simpler than running full pipeline
- Good reference for feature-specific testing

---

## Maintenance Status

✅ **Maintained** - Will work if needed  
🔧 **Specialized** - Only for specific debugging  
📦 **Archived** - Not part of normal workflow

---

**Archived:** October 28, 2025  
**Reason:** Specialized use cases - functionality integrated elsewhere  
**Recommendation:** Use integrated versions unless debugging specific issues

