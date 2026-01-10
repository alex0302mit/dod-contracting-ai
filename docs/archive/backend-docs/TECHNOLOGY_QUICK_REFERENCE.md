# Technology Stack Quick Reference

## Core Technologies at a Glance

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **LLM** | Anthropic Claude | 4 (claude-sonnet-4-20250514) | Primary document generation |
| **Embeddings** | Sentence Transformers | 2.2.0+ | Vector embeddings for RAG |
| **Vector DB** | FAISS | 1.7.4+ | Similarity search index |
| **Web Search** | Tavily API | 0.3.0+ | Real-time market research |
| **PDF Processing** | PyPDF2 | 3.0.0+ | PDF reading/extraction |
| **PDF Forms** | pdfrw | 0.4+ | Form field manipulation |
| **PDF Generation** | ReportLab | 4.0.0+ | Markdown to PDF conversion |
| **Data Processing** | Pandas | 2.0.0+ | Tabular data handling |
| **Spreadsheets** | OpenPyXL | 3.1.0+ | Excel file handling |
| **Word Docs** | python-docx | 0.8.11+ | .docx document handling |
| **Markdown** | Markdown | 3.4.0+ | Markdown parsing |
| **Numerical** | NumPy | 1.24.0+ | Array operations |
| **Environment** | python-dotenv | 1.0.0+ | .env file loading |

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATORS                          │
│  (Coordinate multi-agent workflows)                         │
└────────────┬────────────────────────────────────────────────┘
             │
     ┌───────┴────────────────────────────────────────┐
     │                                                │
┌────▼──────────────────┐      ┌────────────────────▼───┐
│  Specialized Agents   │      │  Support Agents       │
│  • Content writers    │      │  • Quality agent      │
│  • Section generators │      │  • Research agent     │
│  • Form fillers       │      │  • Refinement agent   │
└────┬──────────────────┘      └────┬──────────────────┘
     │                              │
     └──────────────┬───────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼────────┐    ┌──────▼──────┐
    │  Claude API │    │ RAG System   │
    │  (OpenAI)   │    │ • FAISS      │
    │             │    │ • Vector DB  │
    └─────────────┘    │ • Retriever  │
                       └──────┬───────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
              ┌─────▼────┐         ┌─────▼─────┐
              │ Documents│         │ Web Search│
              │ Knowledge│         │  (Tavily) │
              │  Base    │         └───────────┘
              └──────────┘
```

## Dependency Tree

```
requirements.txt
├── anthropic (>=0.18.0)
│   └── For Claude API calls
├── sentence-transformers (>=2.2.0)
│   └── For embedding generation
├── faiss-cpu (>=1.7.4)
│   └── For vector similarity search
├── numpy (>=1.24.0)
│   └── For numerical operations
├── PyPDF2 (>=3.0.0)
│   └── For PDF reading
├── pdfrw (>=0.4)
│   └── For PDF form handling
├── reportlab (>=4.0.0)
│   └── For PDF generation
├── markdown (>=3.4.0)
│   └── For markdown processing
├── pandas (>=2.0.0)
│   └── For data manipulation
├── openpyxl (>=3.1.0)
│   └── For Excel handling
├── python-docx (>=0.8.11)
│   └── For Word document handling
├── pdfkit (>=1.0.0)
│   └── For HTML to PDF conversion
├── python-dotenv (>=1.0.0)
│   └── For environment variables
└── tavily-python (>=0.3.0)
    └── For web search
```

## Key Configuration

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-...          # Required
TAVILY_API_KEY=tvly-...               # Optional (for web search)
```

### LLM Configuration
```python
Model:        claude-sonnet-4-20250514
Temperature:  0.3 (factual) to 0.7 (creative)
Max Tokens:   4,000 to 8,000
Provider:     Anthropic
```

### RAG Configuration
```
Embedding Model:   all-MiniLM-L6-v2
Embedding Dim:     384
Index Type:        FAISS IndexFlatL2
Storage:           /data/vector_db/
Search Top-K:      5-10 results
```

## 30-Second System Overview

1. **Input**: Program requirements and specifications
2. **Agent Layer**: Specialized agents create acquisition documents
3. **RAG Layer**: Retrieves relevant context from knowledge base (FAISS)
4. **LLM Layer**: Claude generates content informed by RAG context
5. **Web Search**: Optional real-time market data from Tavily
6. **Quality Control**: Citation validation, consistency checks, quality scoring
7. **Output**: Markdown + PDF documents with metadata

## Most Important Files

```
agents/
├── base_agent.py                           # Foundation for all agents
├── market_research_report_generator_agent.py
├── acquisition_plan_generator_agent.py
├── igce_generator_agent.py
└── [20+ other specialized agents]

rag/
├── vector_store.py                         # FAISS management
├── retriever.py                            # Query interface
└── document_processor.py                   # Chunking

utils/
├── document_processor.py                   # Post-processing
├── dod_citation_validator.py              # Citation checking
├── consistency_validator.py                # Cross-doc validation
└── convert_md_to_pdf.py                   # Markdown conversion

scripts/
├── generate_all_phases_alms.py            # Master generation
├── setup_rag_system.py                    # RAG initialization
└── [20+ test/utility scripts]
```

## Typical Workflow

```
1. Load Environment
   ↓
2. Initialize RAG System
   ├─ Load FAISS vector index
   └─ Load document chunks
   ↓
3. Initialize Agents
   ├─ Claude API connection
   ├─ Web search tool (optional)
   └─ Quality validators
   ↓
4. Orchestrator Coordinates Generation
   ├─ Research Phase (RAG + Web search)
   ├─ Writing Phase (Content generation)
   ├─ Quality Phase (Evaluation)
   └─ Assembly Phase (Final document)
   ↓
5. Post-Processing
   ├─ PDF generation
   ├─ Citation injection
   └─ Metadata storage
   ↓
6. Output
   └─ Markdown + PDF documents
```

## Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Single document generation | 2-5 min | Depends on complexity |
| Market research report | 5-10 min | Includes web search |
| Complete acquisition package | 15-25 min | All phases |
| RAG vector search | <100ms | Per query |
| PDF generation | 5-30 sec | ReportLab conversion |

## Security Notes

- API keys stored in `.env` (not committed)
- No persistent storage of API responses
- FAISS indices are unencrypted (local storage)
- Generated documents stored locally
- No external database required

## Extension Points

Want to add new features? Key areas:

1. **New Agent**: Inherit from `BaseAgent`, implement `execute()` method
2. **New Tool**: Add to `/agents/tools/` directory
3. **New Validator**: Extend `consistency_validator.py` or `dod_citation_validator.py`
4. **New LLM**: Modify `base_agent.py` to support alternative models
5. **Custom RAG**: Replace FAISS with alternative vector DB

## Troubleshooting Quick Links

- No API key? → Check `.env` file and environment variables
- RAG not working? → Run `setup_rag_system.py` first
- PDF generation fails? → Ensure ReportLab is installed
- Web search errors? → Verify Tavily API key if using search
- Citation validation issues? → Check `dod_citation_validator.py` patterns

---

**Full documentation**: See `TECHNOLOGY_STACK_REPORT.md` for comprehensive details
