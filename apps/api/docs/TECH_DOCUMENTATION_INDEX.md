# Technology Documentation Index

## Overview

This directory now contains comprehensive documentation of all technologies, frameworks, and libraries used in the DoD LLM-Based Acquisition Document Automation System.

## Documentation Files

### 1. TECHNOLOGY_STACK_REPORT.md (Primary Reference)
**Size**: 18KB, 542 lines  
**Purpose**: Complete technical reference for all technologies in the project  

**Contents**:
- Section 1: LLM & AI Integration
  - Anthropic Claude (claude-sonnet-4-20250514)
  - Sentence Transformers (embeddings)
  - Tavily Search API (web search)

- Section 2: Vector Database & RAG
  - FAISS configuration and usage
  - NumPy operations
  - RAG architecture

- Section 3: Document Processing
  - PDF tools (PyPDF2, pdfrw, ReportLab, pdfkit)
  - Word document handling (python-docx)
  - Markdown processing

- Section 4: Data Processing
  - Pandas for tabular data
  - OpenPyXL for Excel files

- Section 5: Agent Architecture
  - BaseAgent framework
  - 30+ specialized agents
  - Orchestrators for workflow coordination

- Section 6: Utilities & Support Libraries
  - Document handling
  - Validation & quality
  - Data extraction
  - Core processing modules

- Section 7: Environment & Configuration
  - Environment variables
  - Dependencies management
  - Directory structure

- Section 8-17: Advanced topics
  - Data storage mechanisms
  - Testing & QA
  - Generation scripts
  - External integrations
  - Deployment & version control
  - Performance characteristics
  - Security notes
  - Critical integration points

**Best For**: Deep dives, understanding integration points, architecture decisions

---

### 2. TECHNOLOGY_QUICK_REFERENCE.md (Quick Lookup)
**Size**: 8.5KB, 221 lines  
**Purpose**: Quick reference guide for developers  

**Contents**:
- Core Technologies at a Glance (table format)
- System Architecture Diagram (ASCII art)
- Dependency Tree (hierarchical)
- Key Configuration (LLM, RAG, Environment)
- 30-Second System Overview
- Most Important Files (quick navigation)
- Typical Workflow (sequence diagram)
- Performance Metrics (quick reference table)
- Security Notes
- Extension Points (how to add features)
- Troubleshooting Quick Links

**Best For**: Quick lookups, new developers, integration decisions

---

## Quick Navigation

### By Purpose

#### I need to understand LLM integration
→ TECHNOLOGY_STACK_REPORT.md Section 1
→ TECHNOLOGY_QUICK_REFERENCE.md "LLM Configuration"

#### I need to understand RAG/Vector Search
→ TECHNOLOGY_STACK_REPORT.md Section 2
→ TECHNOLOGY_QUICK_REFERENCE.md "RAG Configuration"

#### I need to add a new agent
→ TECHNOLOGY_STACK_REPORT.md Section 5 (Agent Architecture)
→ TECHNOLOGY_QUICK_REFERENCE.md "Extension Points"

#### I need to understand document generation
→ TECHNOLOGY_STACK_REPORT.md Section 3 (Document Processing)
→ TECHNOLOGY_STACK_REPORT.md Section 15 (Integration Points)

#### I'm getting an error
→ TECHNOLOGY_QUICK_REFERENCE.md "Troubleshooting Quick Links"
→ TECHNOLOGY_STACK_REPORT.md Section 17 (Security & API Keys)

#### I need to deploy this system
→ TECHNOLOGY_STACK_REPORT.md Section 13 (Deployment)
→ TECHNOLOGY_STACK_REPORT.md Section 7 (Configuration)

### By Technology

#### Anthropic Claude
- TECHNOLOGY_STACK_REPORT.md Section 1.1
- TECHNOLOGY_QUICK_REFERENCE.md Table & Configuration

#### FAISS Vector Database
- TECHNOLOGY_STACK_REPORT.md Section 2.1
- TECHNOLOGY_QUICK_REFERENCE.md Dependency Tree

#### Document Generation (PDF/Markdown)
- TECHNOLOGY_STACK_REPORT.md Section 3
- TECHNOLOGY_QUICK_REFERENCE.md Performance Metrics

#### Agent System
- TECHNOLOGY_STACK_REPORT.md Section 5
- TECHNOLOGY_QUICK_REFERENCE.md Extension Points

---

## Key Metrics at a Glance

| Metric | Value |
|--------|-------|
| Total Python Libraries | 13 major + python-dotenv |
| External APIs | 2 (Anthropic, Tavily) |
| Agent Classes | 30+ |
| Test Scripts | 15+ |
| Documentation Files | 25+ |
| Lines of Code | Thousands |
| Current Python Version | 3.9.13 |
| Primary LLM | Claude Sonnet 4 |
| Vector DB | FAISS |
| Storage Type | File-based (local) |

---

## Technology Categories

### AI/ML Stack
- Anthropic Claude (LLM)
- Sentence Transformers (Embeddings)
- FAISS (Vector Search)
- Tavily (Web Search)

### Document Processing
- PyPDF2
- pdfrw
- ReportLab
- pdfkit
- python-docx
- Markdown

### Data Handling
- Pandas
- OpenPyXL
- NumPy

### System
- python-dotenv (Configuration)
- Standard Library (re, typing, dataclasses, enum)

---

## Configuration Summary

### Required
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Optional
```
TAVILY_API_KEY=tvly-...
```

### Model Settings
```
Model:      claude-sonnet-4-20250514
Temp:       0.3-0.7 (task dependent)
Max Tokens: 4,000-8,000
```

### RAG Settings
```
Embeddings:     all-MiniLM-L6-v2 (384-dim)
Index Type:     FAISS IndexFlatL2
Search Top-K:   5-10
Vector Storage: /data/vector_db/
```

---

## Directory Structure Reference

```
project/
├── agents/                    # All agent implementations
│   ├── base_agent.py         # Foundation class
│   ├── *_generator_agent.py  # Content generators (11)
│   ├── *_orchestrator.py     # Workflow coordinators (7)
│   ├── section_*_agent.py    # RFP section specialists (6)
│   └── tools/
│       └── web_search_tool.py
├── rag/                       # RAG system
│   ├── vector_store.py       # FAISS management
│   ├── retriever.py          # Query interface
│   └── document_processor.py
├── utils/                     # Support utilities
│   ├── document_processor.py
│   ├── consistency_validator.py
│   ├── dod_citation_validator.py
│   ├── convert_md_to_pdf.py
│   └── [other utilities]
├── core/                      # Core modules
│   ├── market_research.py
│   ├── add_citations.py
│   └── evaluate_report.py
├── scripts/                   # Standalone executables
│   ├── generate_all_phases_alms.py
│   └── [other scripts]
├── data/
│   ├── documents/            # RAG knowledge base
│   └── vector_db/            # FAISS indices
├── outputs/                   # Generated documents
├── .env                       # Configuration
└── requirements.txt           # Dependencies
```

---

## Related Documentation

Also see in this repository:
- `README.md` - Project overview
- `GETTING_STARTED.md` - Setup guide
- `AGENT_SYSTEM_README.md` - Agent system details
- `RAG_AND_AGENT_PROTOCOLS.md` - RAG integration specs
- `AGENT_WORKFLOW_PROCESS_FLOWS.md` - Workflow diagrams
- `/docs/` - Additional guides and specifications

---

## How to Use This Documentation

### For Quick Answers
1. Check TECHNOLOGY_QUICK_REFERENCE.md first
2. Look for your specific technology in the tables
3. Follow links to TECHNOLOGY_STACK_REPORT.md for details

### For Deep Understanding
1. Start with TECHNOLOGY_STACK_REPORT.md Section 1-5
2. Read relevant sections based on your interest
3. Review integration points in Section 15
4. Check code examples in actual source files

### For Problem Solving
1. Check TECHNOLOGY_QUICK_REFERENCE.md troubleshooting section
2. Search TECHNOLOGY_STACK_REPORT.md for your issue
3. Review source code for that component
4. Check project README for common issues

---

## Technology Stack Summary (TL;DR)

This is a **multi-agent LLM system** for DoD acquisition automation that combines:

1. **Claude API** for intelligent content generation
2. **FAISS** for vector similarity search (RAG)
3. **Sentence Transformers** for embeddings
4. **30+ specialized agents** for different document types
5. **Professional PDF generation** (ReportLab)
6. **Web search** (Tavily) for market data
7. **Quality validation** (citations, consistency, scoring)

All running locally with file-based storage and configuration.

---

## Version History

- **Created**: October 22, 2025
- **Scope**: Complete technology stack documentation
- **Coverage**: All 13+ libraries, 30+ agents, 7 orchestrators
- **Status**: Complete and comprehensive

---

**Start here**: TECHNOLOGY_QUICK_REFERENCE.md (quick overview)  
**Go deeper**: TECHNOLOGY_STACK_REPORT.md (comprehensive reference)
