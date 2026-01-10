# System Architecture - DoD Procurement Document Generation

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                                   │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    React Front-End                              │    │
│  │                  (dod_contracting_front_end/)                   │    │
│  │                                                                  │    │
│  │  Components:                                                     │    │
│  │  • ProcurementHub      → Dashboard                              │    │
│  │  • ProjectDashboard    → Project list                           │    │
│  │  • ProcurementTracker  → Phase tracking                         │    │
│  │  • DocumentChecklist   → Document management                    │    │
│  │  • SegmentedTrackerBar → Visual progress                        │    │
│  │                                                                  │    │
│  │  Services:                                                       │    │
│  │  • api.ts              → HTTP API calls                         │    │
│  │  • websocket.ts        → WebSocket client                       │    │
│  │  • AuthContext         → User authentication                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                          │                │                              │
│                     HTTP/HTTPS      WebSocket                            │
└─────────────────────────┼────────────────┼──────────────────────────────┘
                          │                │
                          ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVER                                      │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                          │    │
│  │                      (backend/main.py)                          │    │
│  │                                                                  │    │
│  │  REST API Endpoints:                                            │    │
│  │  ┌────────────────────┐  ┌─────────────────────┐               │    │
│  │  │  Authentication    │  │    Projects         │               │    │
│  │  │  • POST /login     │  │  • GET /projects    │               │    │
│  │  │  • POST /register  │  │  • POST /projects   │               │    │
│  │  │  • GET /me         │  │  • GET /projects/:id│               │    │
│  │  └────────────────────┘  └─────────────────────┘               │    │
│  │                                                                  │    │
│  │  ┌────────────────────┐  ┌─────────────────────┐               │    │
│  │  │  Document Gen      │  │  Notifications      │               │    │
│  │  │  • POST /generate  │  │  • GET /notifications│              │    │
│  │  │  • GET /documents  │  │  • PATCH /read      │               │    │
│  │  └────────────────────┘  └─────────────────────┘               │    │
│  │                                                                  │    │
│  │  WebSocket:                                                      │    │
│  │  ┌────────────────────────────────────────────┐                │    │
│  │  │  WS /ws/{project_id}                       │                │    │
│  │  │  • Real-time progress updates              │                │    │
│  │  │  • Generation status changes               │                │    │
│  │  │  • Error notifications                     │                │    │
│  │  └────────────────────────────────────────────┘                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                          │                                               │
│                          │                                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Middleware Layer                             │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │    │
│  │  │ JWT Auth     │  │ CORS         │  │ Rate Limit   │         │    │
│  │  │ Verify Token │  │ Allow Origins│  │ (future)     │         │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                          │                                               │
│                          ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Service Layer                                │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────┐  ┌──────────────────────────┐    │    │
│  │  │ DocumentGeneratorService │  │ WebSocketManager         │    │    │
│  │  │ • generate_pws()         │  │ • send_progress_update() │    │    │
│  │  │ • generate_all_phases()  │  │ • send_complete()        │    │    │
│  │  │ • refine_document()      │  │ • broadcast()            │    │    │
│  │  └──────────────────────────┘  └──────────────────────────┘    │    │
│  │                │                                                 │    │
│  │                │ calls                                           │    │
│  │                ▼                                                 │    │
│  │  ┌────────────────────────────────────────────────────────┐    │    │
│  │  │         YOUR EXISTING AI AGENTS                        │    │    │
│  │  │         (scripts/)                                     │    │    │
│  │  │                                                         │    │    │
│  │  │  • requirements_agent.py  → Analyze requirements       │    │    │
│  │  │  • pws_agent.py          → Generate PWS                │    │    │
│  │  │  • rfp_agent.py          → Generate RFP                │    │    │
│  │  │  • refinement_agent.py   → Quality improvement         │    │    │
│  │  │  • evaluation_agent.py   → Score documents             │    │    │
│  │  │  • generate_all_phases_alms.py → Orchestrate all       │    │    │
│  │  └────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                          │                                               │
│                          ▼                                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Data Layer                                   │    │
│  │                                                                  │    │
│  │  SQLAlchemy ORM Models:                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │    │
│  │  │ User         │  │ Project      │  │ Document     │         │    │
│  │  │ • id         │  │ • id         │  │ • id         │         │    │
│  │  │ • email      │  │ • name       │  │ • name       │         │    │
│  │  │ • role       │  │ • status     │  │ • status     │         │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │    │
│  │  │ Phase        │  │ Step         │  │ Notification │         │    │
│  │  │ • id         │  │ • id         │  │ • id         │         │    │
│  │  │ • name       │  │ • name       │  │ • message    │         │    │
│  │  │ • status     │  │ • status     │  │ • read       │         │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘         │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                                 │
│                                                                          │
│  Tables:                                                                 │
│  • users                  → User accounts and roles                      │
│  • procurement_projects   → Main project records                        │
│  • procurement_phases     → Project phases                              │
│  • procurement_steps      → Individual workflow steps                   │
│  • project_documents      → Document checklist                          │
│  • document_uploads       → File versions                               │
│  • document_approvals     → Approval workflow                           │
│  • notifications          → User notifications                          │
│  • audit_log              → Change tracking                             │
│                                                                          │
│  Indexes, Foreign Keys, Triggers all configured                         │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      File System                                         │
│                                                                          │
│  uploads/                  → User uploaded files                         │
│  generated_documents/      → AI-generated PDFs/DOCX                      │
│  └─ project_abc123/                                                      │
│     ├─ pws_20251031.pdf                                                  │
│     ├─ rfp_20251031.pdf                                                  │
│     └─ ...                                                               │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      External Services                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Anthropic    │  │ OpenAI       │  │ Email        │                  │
│  │ Claude API   │  │ GPT-4 API    │  │ SMTP Server  │                  │
│  │ (Your agents)│  │ (Your agents)│  │ (Notifications)                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Document Generation

```
1. USER ACTION
   User clicks "Generate PWS" button
   │
   ▼
2. FRONTEND
   React Component calls API
   projectsApi.generateDocument(projectId, 'pws')
   │
   ▼
3. HTTP REQUEST
   POST /api/projects/{id}/generate-document
   Headers: Authorization: Bearer {JWT_TOKEN}
   Body: { document_type: "pws" }
   │
   ▼
4. BACKEND - Authentication
   JWT Middleware verifies token
   Extracts user from token
   Checks user permissions
   │
   ▼
5. BACKEND - API Handler
   main.py: generate_document()
   • Validates project exists
   • Checks user has access
   • Calls DocumentGeneratorService
   │
   ▼
6. BACKEND - Service Layer
   document_generator.generate_pws()
   │
   ├─► WebSocket: "generation_started"
   │
   ├─► Progress 10%: "Analyzing requirements..."
   │   Calls YOUR requirements_agent.py
   │   └─► Calls Anthropic Claude API
   │
   ├─► Progress 40%: "Generating PWS..."
   │   Calls YOUR pws_agent.py
   │   └─► Calls OpenAI GPT-4 API
   │
   ├─► Progress 70%: "Refining document..."
   │   Calls YOUR refinement_agent.py
   │   └─► Multi-iteration improvement
   │
   ├─► Progress 90%: "Creating PDF..."
   │   Generates PDF from markdown
   │   Saves to file system
   │
   └─► WebSocket: "generation_complete"
       URL: /files/pws_abc123.pdf
   │
   ▼
7. DATABASE UPDATE
   • Create DocumentUpload record
   • Update ProjectDocument status
   • Create Notification
   • Log to AuditLog
   │
   ▼
8. WEBSOCKET BROADCAST
   All connected clients for this project receive:
   {
     "type": "generation_complete",
     "document_url": "/files/pws_abc123.pdf"
   }
   │
   ▼
9. FRONTEND UPDATE
   • WebSocket listener receives message
   • Updates UI progress bar to 100%
   • Shows download button
   • Displays success notification
   │
   ▼
10. USER DOWNLOADS
    User clicks download button
    Browser downloads /files/pws_abc123.pdf
```

## Authentication Flow

```
┌──────────┐
│  User    │
│  Login   │
└────┬─────┘
     │
     │ 1. POST /api/auth/login
     │    {email, password}
     ▼
┌─────────────────┐
│  FastAPI        │
│  Auth Handler   │
└────┬────────────┘
     │
     │ 2. Query database
     ▼
┌─────────────────┐
│  PostgreSQL     │
│  users table    │
└────┬────────────┘
     │
     │ 3. Return user
     ▼
┌─────────────────┐
│  Verify         │
│  Password       │
│  (bcrypt)       │
└────┬────────────┘
     │
     │ 4. Generate JWT
     ▼
┌─────────────────┐
│  JWT Token      │
│  {user_id, exp} │
│  Signed         │
└────┬────────────┘
     │
     │ 5. Return token
     ▼
┌─────────────────┐
│  Frontend       │
│  Stores in      │
│  localStorage   │
└────┬────────────┘
     │
     │ 6. All future requests
     │    Header: Authorization: Bearer {token}
     ▼
┌─────────────────┐
│  Backend        │
│  Verifies token │
│  on each request│
└─────────────────┘
```

## Technology Stack Summary

### Frontend
- **Framework**: React 18.3
- **Language**: TypeScript
- **Build Tool**: Vite 5.4
- **UI Library**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS 3.4
- **State**: React Context API
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API

### Backend
- **Framework**: FastAPI 0.104
- **Language**: Python 3.11+
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15+
- **Authentication**: JWT (python-jose)
- **Password Hash**: bcrypt (passlib)
- **WebSocket**: FastAPI built-in

### AI Layer
- **Orchestration**: LangChain
- **LLM APIs**: Anthropic Claude, OpenAI GPT-4
- **Document Gen**: Your existing agents
- **Refinement**: Recursive improvement cycles

### Infrastructure
- **Database**: PostgreSQL
- **File Storage**: Local filesystem (can migrate to S3)
- **Cache**: (Optional) Redis
- **Task Queue**: (Optional) Celery
- **Monitoring**: (Future) Sentry, DataDog

## Deployment Architecture

```
Production Deployment (Example)

┌─────────────────────────────────────────────────────┐
│                  Load Balancer                       │
│                  (Nginx/HAProxy)                     │
└────────────┬──────────────────────┬──────────────────┘
             │                      │
             ▼                      ▼
┌──────────────────────┐  ┌──────────────────────┐
│  Frontend Server 1   │  │  Frontend Server 2   │
│  (Static Files)      │  │  (Static Files)      │
│  Nginx/Vercel/Netlify│  │  Nginx/Vercel/Netlify│
└──────────────────────┘  └──────────────────────┘
             │                      │
             └──────────┬───────────┘
                        │ API Calls
                        ▼
             ┌────────────────────┐
             │   API Gateway      │
             │   (Future)         │
             └────────┬───────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Backend      │ │ Backend      │ │ Backend      │
│ Instance 1   │ │ Instance 2   │ │ Instance 3   │
│ (Docker)     │ │ (Docker)     │ │ (Docker)     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌───────────────────┐
              │  PostgreSQL       │
              │  (Primary)        │
              └─────────┬─────────┘
                        │
                        │ Replication
                        ▼
              ┌───────────────────┐
              │  PostgreSQL       │
              │  (Replica)        │
              └───────────────────┘

              ┌───────────────────┐
              │  Redis Cache      │
              │  (Session Store)  │
              └───────────────────┘

              ┌───────────────────┐
              │  S3 Storage       │
              │  (Files)          │
              └───────────────────┘

              ┌───────────────────┐
              │  Celery Workers   │
              │  (Background Jobs)│
              └───────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Security Layers                      │
│                                                      │
│  1. Network Layer                                   │
│     • HTTPS/TLS encryption                          │
│     • Firewall rules                                │
│     • DDoS protection                               │
│                                                      │
│  2. Application Layer                               │
│     • JWT token authentication                      │
│     • Password hashing (bcrypt)                     │
│     • CORS restrictions                             │
│     • Rate limiting                                 │
│                                                      │
│  3. Authorization Layer                             │
│     • Role-based access control (RBAC)              │
│     • Project-level permissions                     │
│     • Action-level permissions                      │
│                                                      │
│  4. Data Layer                                      │
│     • SQL injection prevention (ORM)                │
│     • Database encryption at rest                   │
│     • Regular backups                               │
│     • Audit logging                                 │
│                                                      │
│  5. File Security                                   │
│     • Virus scanning (future)                       │
│     • File type validation                          │
│     • Size limits                                   │
│     • Access control on downloads                   │
└─────────────────────────────────────────────────────┘
```

## Scalability Considerations

**Current Capacity:**
- ~100 concurrent users
- ~10 simultaneous document generations
- Single server deployment

**Scaling Path:**

**Phase 1** (100-500 users):
- Add Redis for session caching
- Add Celery for background tasks
- Horizontal scale backend (2-3 instances)

**Phase 2** (500-2000 users):
- Add load balancer
- Database read replicas
- CDN for static files
- Move file storage to S3

**Phase 3** (2000+ users):
- Kubernetes orchestration
- Multi-region deployment
- Database sharding
- Dedicated AI processing cluster

This architecture is designed to start simple but scale as needed!
