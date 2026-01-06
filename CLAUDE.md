# DoD Contracting AI Application - Claude Memory

## Project Overview
AI-powered DoD acquisition document generation system that automates procurement workflows using 40+ specialized agents, RAG-based context retrieval, and compliance validation.

## Quick Start
```bash
# Start everything
./start_all.sh

# Or separately:
./start_backend.sh   # Backend on http://localhost:8000
./start_frontend.sh  # Frontend on http://localhost:5173
```

## Architecture

### Tech Stack
| Layer | Technology |
|-------|------------|
| Backend | FastAPI 0.104.1, Python 3.9+, SQLAlchemy ORM |
| Frontend | React 18.3.1, TypeScript, Vite, Tailwind CSS |
| LLM | Anthropic Claude (claude-sonnet-4-20250514) |
| Vector DB | FAISS (CPU-based) for RAG embeddings |
| UI Components | shadcn/ui, Radix UI, Tiptap editor |
| Auth | JWT with role-based access control |

### Directory Structure
```
├── backend/
│   ├── main.py              # FastAPI app (3,260 lines)
│   ├── agents/              # 40+ specialized agents
│   ├── services/            # Core business logic
│   ├── rag/                 # Vector store & retrieval
│   ├── models/              # SQLAlchemy ORM models
│   ├── config/              # YAML/JSON configurations
│   └── utils/               # 19 utility modules
├── dod_contracting_front_end/src/
│   ├── components/          # React components
│   │   ├── AIContractingUI.tsx   # Main container
│   │   ├── LiveEditor.tsx        # Document editor
│   │   ├── editor/               # 25 editor components
│   │   └── procurement/          # 22 procurement components
│   ├── services/api.ts      # 50+ API endpoints
│   ├── hooks/               # Custom React hooks
│   └── contexts/            # Auth & state contexts
└── data/                    # Exports & document storage
```

## Key Services

### Agent Router (`backend/services/agent_router.py`)
Routes documents to 41+ specialized agents with pattern matching and fallbacks.

### Generation Coordinator (`backend/services/generation_coordinator.py`)
Orchestrates multi-document generation across 4 procurement phases.

### Phase Detector (`backend/services/phase_detector.py`)
Analyzes document selection to determine procurement phase with confidence scoring.

### RAG Service (`backend/services/rag_service.py`)
Wraps FAISS vector store for context retrieval from uploaded documents.

## Specialized Agents

### RFP Section Generators
- `SectionLGeneratorAgent` - Instructions to Offerors
- `SectionMGeneratorAgent` - Evaluation Factors
- `SectionBGeneratorAgent` - Supplies/Services & Prices
- `SectionHGeneratorAgent` - Special Contract Requirements
- `SectionIGeneratorAgent` - Contract Clauses
- `SectionKGeneratorAgent` - Representations & Certifications

### Work Statement Agents
- `PWSWriterAgent` - Performance Work Statement
- `SOWWriterAgent` - Statement of Work
- `SOOWriterAgent` - Statement of Objectives

### Pre-Solicitation Agents
- `MarketResearchReportGeneratorAgent`
- `AcquisitionPlanGeneratorAgent`
- `SourcesSoughtGeneratorAgent`
- `IGCEGeneratorAgent` - Cost Estimation

### Quality & Orchestration
- `QualityAgent` - FAR/DFARS compliance checking
- `RefinementAgent` - Iterative improvement
- `RFPOrchestrator`, `SolicitationPackageOrchestrator`

## Database Models

### Core Entities
- `User` - Roles: contracting_officer, program_manager, approver, viewer
- `ProcurementProject` - Main project with status tracking
- `ProcurementPhase` - Pre-solicitation, solicitation, post-solicitation, award
- `ProjectDocument` - Documents with versions and approvals
- `DocumentUpload` - File uploads with RAG processing

## API Endpoints (Key Routes)

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Current user info

### Projects & Documents
- `GET/POST /api/projects` - List/create projects
- `GET /api/projects/{id}/documents` - Project documents
- `POST /api/generate-documents` - Generate documents
- `POST /api/analyze-generation-plan` - Phase analysis

### RAG & Knowledge Base
- `POST /api/rag/upload` - Upload to knowledge base
- `POST /api/rag/search` - Search documents
- `GET /api/rag/stats` - Vector store statistics

### Export
- `GET /api/export/{id}/pdf` - Download PDF
- `GET /api/export/{id}/docx` - Download DOCX

## Configuration Files

| File | Purpose |
|------|---------|
| `backend/config/document_agent_mapping.yaml` | Agent → Document mapping (385 lines) |
| `backend/config/phase_definitions.yaml` | Procurement phases & requirements |
| `backend/config/document_dependencies.json` | Cross-document dependency graph |
| `.env` | API keys (ANTHROPIC_API_KEY, TAVILY_API_KEY) |

## Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Test coverage
# Phase 1 (Agent Infrastructure): 51/51 passing
# Phase 2 (API Integration): 6/6 passing
# Phase 4 (Collaboration): 17 tests
```

## Current Development

### Branch: `feature/main_agents_RFP`

### Recent Changes
- Enhanced quality agent with compliance checking
- Live editor improvements with copilot integration
- Upload center file handling
- Export formatter updates
- User role management (contracting_officer assignment)

### Modified Files
- `backend/main.py` - API endpoints
- `backend/models/procurement.py` - Project models
- `backend/models/user.py` - User roles
- `dod_contracting_front_end/src/components/AIContractingUI.tsx`
- `dod_contracting_front_end/src/components/LiveEditor.tsx`
- `dod_contracting_front_end/src/services/api.ts`

### New Files
- `backend/scripts/bootstrap_users.py` - User initialization
- `dod_contracting_front_end/src/components/admin/` - Admin panel
- `AssignOfficerDialog.tsx` - Officer assignment UI

## Code Patterns

### Adding a New Agent
1. Create `backend/agents/your_agent.py` inheriting from `BaseAgent`
2. Add mapping in `backend/config/document_agent_mapping.yaml`
3. Register in `backend/services/agent_router.py`

### Adding API Endpoint
1. Add route in `backend/main.py`
2. Create service method if needed
3. Add frontend API call in `dod_contracting_front_end/src/services/api.ts`

### Frontend Component Pattern
- Use shadcn/ui components from `components/ui/`
- State management via React Query hooks
- Auth context from `contexts/AuthContext.tsx`

## Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Claude API
TAVILY_API_KEY=tvly-...          # Web search
DATABASE_URL=sqlite:///...        # Database (optional, defaults to SQLite)
```

## Common Commands

```bash
# Development
cd backend && uvicorn main:app --reload --port 8000
cd dod_contracting_front_end && npm run dev

# Database
# Auto-created on startup via SQLAlchemy

# Lint/Format
cd dod_contracting_front_end && npm run lint
```

## Documentation
- [START_HERE.md](START_HERE.md) - Quick start guide
- [HOW_TO_USE.md](HOW_TO_USE.md) - Complete usage guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Phase completion status
- [MULTI_AGENT_STRATEGY.md](MULTI_AGENT_STRATEGY.md) - Agent architecture
- [PHASE_4_PLAN.md](PHASE_4_PLAN.md) - Cross-document collaboration
