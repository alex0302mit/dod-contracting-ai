# DoD Contracting AI Application - Claude Memory

## Project Overview
AI-powered DoD acquisition document generation system that automates procurement workflows using 44 specialized agents, RAG-based context retrieval, document lineage tracking, and compliance validation.

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
| Document Processing | Docling for PDF/document parsing |
| UI Components | shadcn/ui, Radix UI, Tiptap editor |
| Auth | JWT with role-based access control |
| Real-time | WebSocket for live updates |

### Directory Structure
```
├── apps/
│   ├── api/                      # FastAPI backend (main.py: 5,436 lines)
│   │   ├── agents/               # 44 specialized agents
│   │   ├── services/             # 13 core services
│   │   ├── models/               # 7 database models
│   │   ├── rag/                  # Vector store & Docling retrieval
│   │   ├── config/               # YAML/JSON configurations
│   │   ├── utils/                # 17 utility modules
│   │   └── templates/            # 29 document templates
│   └── web/                      # React frontend
│       └── src/
│           ├── components/       # 162 React components
│           │   ├── admin/        # Admin panel & analytics
│           │   ├── dashboard/    # Dashboard views
│           │   ├── editor/       # Live editor & issue management
│           │   ├── procurement/  # Procurement workflow
│           │   ├── guided/       # Guided workflow flows
│           │   ├── comparison/   # Agent comparison view
│           │   └── ui/           # shadcn/ui components
│           ├── services/api.ts   # 55+ API client methods
│           ├── hooks/            # Custom React hooks (analytics, stats)
│           └── contexts/         # Auth, navigation & state contexts
├── tools/
│   ├── testing/                  # 40+ test files
│   ├── migrations/               # Database migrations
│   └── setup/                    # Database seeding & RAG setup
├── data/exports/                 # Generated document exports
└── backend -> apps/api           # Symlink for compatibility
```

## Key Services

### Agent Router (`apps/api/services/agent_router.py`)
Routes documents to 44 specialized agents with pattern matching and fallbacks.

### Generation Coordinator (`apps/api/services/generation_coordinator.py`)
Orchestrates multi-document generation with dependency resolution and task queuing.

### Phase Detector (`apps/api/services/phase_detector.py`)
Analyzes document selection to determine procurement phase with confidence scoring.

### RAG Service (`apps/api/services/rag_service.py`)
FAISS vector store with Docling-based document processing for intelligent retrieval.

### Phase Gate Service (`apps/api/services/phase_gate_service.py`)
Controls phase transitions with approval gating and validation.

### Export Service (`apps/api/services/export_service.py`)
Generates PDF, DOCX, and JSON exports from markdown content.

### WebSocket Manager (`apps/api/services/websocket_manager.py`)
Real-time updates for document generation and collaboration.

### Agent Comparison Service (`apps/api/services/agent_comparison_service.py`)
A/B testing framework for comparing agent variants.

## Specialized Agents (44 Total)

### RFP Section Generators
- `SectionBGeneratorAgent` - Supplies/Services & Prices
- `SectionHGeneratorAgent` - Special Contract Requirements
- `SectionIGeneratorAgent` - Contract Clauses
- `SectionKGeneratorAgent` - Representations & Certifications
- `SectionLGeneratorAgent` - Instructions to Offerors
- `SectionMGeneratorAgent` - Evaluation Factors

### Work Statement Agents
- `PWSWriterAgent` - Performance Work Statement
- `SOWWriterAgent` - Statement of Work
- `SOOWriterAgent` - Statement of Objectives
- `PWSOrchestratorAgent`, `SOWOrchestratorAgent`, `SOOOrchestratorAgent`

### Pre-Solicitation Agents
- `MarketResearchReportGeneratorAgent`
- `AcquisitionPlanGeneratorAgent`
- `SourcesSoughtGeneratorAgent`
- `IGCEGeneratorAgent` - Independent Government Cost Estimate
- `IndustryDayGeneratorAgent`
- `RFIGeneratorAgent`

### Post-Solicitation Agents
- `SourceSelectionPlanGeneratorAgent`
- `EvaluationScorecardGeneratorAgent`
- `SSDDGeneratorAgent` - Source Selection Decision Document
- `AwardNotificationGeneratorAgent`
- `DebriefingGeneratorAgent`
- `AmendmentGeneratorAgent`

### Quality & Orchestration
- `QualityAgent` - FAR/DFARS compliance checking
- `RefinementAgent` - Iterative improvement
- `QAManagerAgent` - Quality assurance manager
- `QASPGeneratorAgent` - Quality Assurance Surveillance Plan
- `PreSolicitationOrchestrator`
- `SolicitationPackageOrchestrator`
- `PostSolicitationOrchestrator`
- `RFPOrchestratorAgent`

### Form Generators
- `SF26GeneratorAgent` - Award/Contract Form
- `SF33GeneratorAgent` - Solicitation, Offer and Award
- `PPQGeneratorAgent` - Past Performance Questionnaire

## Database Models (7 Total)

### Core Entities (`apps/api/models/`)
- `User` - Roles: admin, contracting_officer, program_manager, approver, viewer
- `ProcurementProject` - Main project with status tracking
- `ProcurementPhase` - PRE_SOLICITATION, SOLICITATION, POST_SOLICITATION
- `ProcurementStep` - Workflow steps within phases
- `ProjectDocument` - Documents with AI generation tracking
- `DocumentUpload` - File uploads with RAG processing
- `DocumentApproval` - Approval workflows with routing

### Compliance & Tracking
- `DocumentLineage` - Source-to-derived document relationships
- `AuditLog` - All system changes for compliance
- `Notification` - User alerts and system messages

## API Endpoints (95+ Total)

### Authentication & User
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Current user info
- `GET /api/users/me/stats` - Personal analytics (documents generated, hours saved)

### Admin
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}/role` - Update user role
- `POST /api/admin/bootstrap` - Create first admin
- `DELETE /api/admin/users/{id}` - Delete user
- `GET /api/admin/analytics` - Organization-wide analytics dashboard

### Projects & Documents
- `GET/POST /api/projects` - List/create projects
- `GET /api/projects/{id}/documents` - Project documents
- `POST /api/documents/{id}/generate` - Generate document
- `GET /api/documents/{id}/generation-status` - Check status

### Document Generation
- `POST /api/generate-documents` - Generate selected documents
- `POST /api/analyze-generation-plan` - Phase analysis
- `POST /api/projects/{id}/generate-batch` - Batch generation

### Approvals & Phase Management
- `POST /api/documents/{id}/request-approval` - Request approval
- `POST /api/approvals/{id}/approve` - Approve document
- `GET /api/phases/{id}/validate-transition` - Validate transition
- `POST /api/phase-transitions/{id}/approve` - Approve transition

### RAG & Knowledge Base
- `POST /api/rag/upload` - Upload to knowledge base
- `POST /api/rag/search` - Search documents
- `GET /api/rag/stats` - Vector store statistics

### Document Lineage
- `GET /api/documents/{id}/lineage` - Document lineage
- `GET /api/documents/{id}/timeline` - Document timeline
- `GET /api/documents/{id}/influence-graph` - Influence visualization

### Export
- `GET /api/export/{id}/pdf` - Download PDF
- `GET /api/export/{id}/docx` - Download DOCX
- `POST /api/export/compliance-report` - Generate compliance report

### Agent Comparison
- `POST /api/comparison/start` - Start A/B comparison
- `GET /api/comparison/results/{id}` - Get comparison results

### WebSocket
- `WS /ws/{project_id}` - Real-time project updates
- `WS /api/ws/guided-flow/{id}` - Guided flow updates

## Configuration Files

| File | Purpose |
|------|---------|
| `apps/api/config/document_agent_mapping.yaml` | Agent → Document mapping (385+ lines) |
| `apps/api/config/phase_definitions.yaml` | Procurement phases & requirements |
| `apps/api/config/document_dependencies.json` | Cross-document dependency graph |
| `apps/api/config/copilot_config.json` | AI copilot configuration |
| `.env` | API keys (ANTHROPIC_API_KEY, TAVILY_API_KEY) |

## Testing

```bash
# Run all tests
cd tools/testing
python run_all_tests.py

# Run specific test suites
python -m pytest tools/testing/test_all_agents.py -v
python -m pytest tools/testing/test_api_endpoints.py -v
python -m pytest tools/testing/test_integration.py -v

# Test categories available:
# - Unit tests: test_*_agent.py (44 agents)
# - API tests: test_api_endpoints.py (90+ endpoints)
# - Integration: test_integration.py, test_full_pipeline.py
# - Services: test_all_services.py
# - Database: test_database_models.py
```

## Code Patterns

### Adding a New Agent
1. Create `apps/api/agents/your_agent.py` inheriting from `BaseAgent`
2. Implement `generate()` and `refine()` methods
3. Add mapping in `apps/api/config/document_agent_mapping.yaml`
4. Register in `apps/api/services/agent_router.py`

### Adding API Endpoint
1. Add route in `apps/api/main.py`
2. Create service method in `apps/api/services/` if needed
3. Add frontend API call in `apps/web/src/services/api.ts`
4. Add TypeScript types in `apps/web/src/types/`

### Frontend Component Pattern
- Use shadcn/ui components from `components/ui/`
- State management via React Query hooks
- Auth context from `contexts/AuthContext.tsx`
- Follow existing patterns in `components/procurement/`

### Document Generation Flow
1. User selects documents in UI
2. `analyze-generation-plan` determines phase & dependencies
3. `generation_coordinator` queues tasks
4. `agent_router` dispatches to appropriate agents
5. WebSocket broadcasts progress updates
6. Results saved with lineage tracking

## Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Claude API (required)
TAVILY_API_KEY=tvly-...          # Web search (optional)
DATABASE_URL=sqlite:///...        # Database (defaults to SQLite)
JWT_SECRET=...                    # JWT signing key
```

## Common Commands

```bash
# Development
cd apps/api && uvicorn main:app --reload --port 8000
cd apps/web && npm run dev

# Database
python tools/setup/seed_database.py
python tools/migrations/run_migrations.py

# RAG Setup
python tools/setup/setup_rag.py

# Lint/Format
cd apps/web && npm run lint
cd apps/api && black . && isort .
```

## Key Features

### Document Lineage Tracking
- Tracks source → derived document relationships
- Supports influence types: context, template, regulation, data_source, reference
- Provides timeline and influence graph visualization

### Phase Transition Management
- Validates all required documents before phase transition
- Supports approval workflows for transitions
- Audit trail for compliance

### Real-time Collaboration
- WebSocket-based live updates
- Generation progress broadcasting
- Multi-user editing support

### Quality Assurance
- FAR/DFARS compliance checking via QualityAgent
- Hallucination detection
- Vague language identification and fixing
- Citation validation

### Export Capabilities
- PDF export with proper formatting
- DOCX export for editing
- Compliance report generation
- Batch export for multiple documents

## Recent Enhancements

### Analytics & Reporting
- Admin analytics dashboard with KPIs, trends, and top contributors
- Personal user statistics (documents generated, hours saved, projects)
- CSV export for analytics data
- Time savings calculation based on document types

### Editor Issue Management
- Grouped issues panel with collapsible sections by type
- Batch fix preview modal with parallel AI fix generation
- Inline issue popover on highlighted text
- Floating navigation bar for issue traversal (keyboard shortcuts)
- Enhanced vague language detection patterns

### Core Features
- Document lineage tracking with RAG chunk references
- Docling-based advanced PDF processing
- Agent comparison service for A/B testing
- Phase transition approval workflows
- Admin panel for user management
- Dashboard with metrics and quick actions
- Guided workflow with step-by-step instructions
- Audit logging for DoD compliance
- Notification system with email integration

## Frontend Components (New)

### Admin Components
- `AdminAnalytics` - Organization-wide analytics dashboard with charts

### Editor Components
- `BatchFixPreviewModal` - Preview and apply AI-generated fixes for multiple issues
- `GroupedIssuesPanel` - Issues organized by type with bulk fix actions
- `IssueFloatingNav` - Floating navigation for issue traversal
- `IssueInlinePopover` - Popover for highlighted issues with fix/dismiss actions

## React Hooks

### Analytics Hooks
- `useAdminAnalytics` - Fetches org-wide analytics with configurable time period
- `useUserStats` - Fetches personal user statistics with lazy loading
