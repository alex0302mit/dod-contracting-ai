# DoD Procurement System - Complete Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Data Flow](#data-flow)
5. [Authentication Flow](#authentication-flow)
6. [Document Generation Pipeline](#document-generation-pipeline)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Frontend Architecture](#frontend-architecture)
10. [Deployment Guide](#deployment-guide)

---

## System Overview

The DoD Procurement System is a full-stack application designed to streamline the Department of Defense procurement process. It automates document generation using AI agents and provides real-time progress tracking through a modern web interface.

### Key Features:
- **AI-Powered Document Generation**: Uses Claude AI to generate procurement documents (PWS, IGCE, RFP, etc.)
- **Real-time Updates**: WebSocket connections provide live progress updates during document generation
- **Role-Based Access Control**: Four distinct user roles with different permissions
- **Multi-Phase Tracking**: Tracks projects through 6 procurement phases
- **Document Versioning**: Maintains history of all generated documents

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                               │
│                    (React + TypeScript + Vite)                        │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Dashboard   │  │   Tracker    │  │  AI Studio   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────────────────────────────────────────────┐           │
│  │          API Service Layer (api.ts)                   │           │
│  │  - Authentication  - Projects  - WebSocket            │           │
│  └──────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                              ▲  │
                              │  │ HTTP/HTTPS (REST API)
                              │  │ WebSocket (Real-time)
                              │  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND API SERVER                              │
│                    (Python FastAPI + Uvicorn)                         │
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │  Auth Middleware   │  │  CORS Middleware   │                     │
│  └────────────────────┘  └────────────────────┘                     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │                  API ENDPOINTS                            │        │
│  │  /api/auth/*     - Authentication                        │        │
│  │  /api/projects/* - Project CRUD                          │        │
│  │  /ws/{id}        - WebSocket connection                  │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │               SERVICES LAYER                              │        │
│  │  - DocumentGeneratorService (AI integration)             │        │
│  │  - WebSocketManager (Real-time updates)                  │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                              ▲  │
                              │  │ SQLAlchemy ORM
                              │  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                                  │
│                    (PostgreSQL Database)                              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    users     │  │   projects   │  │  documents   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    phases    │  │     steps    │  │ permissions  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘

                              ▲  │
                              │  │ API Calls
                              │  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AI AGENTS LAYER                                 │
│                   (Your Existing Python Scripts)                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  scripts/generate_all_phases_alms.py                      │       │
│  │  ┌─────────────────┐  ┌─────────────────┐                │       │
│  │  │ Phase 0:        │  │ Phase 1:        │                │       │
│  │  │ Requirements    │  │ Pre-Solicitation│                │       │
│  │  └─────────────────┘  └─────────────────┘                │       │
│  │                                                            │       │
│  │  ┌─────────────────┐  ┌─────────────────┐                │       │
│  │  │ Phase 2:        │  │ Phase 3:        │                │       │
│  │  │ Solicitation    │  │ Post-Solicitation│               │       │
│  │  └─────────────────┘  └─────────────────┘                │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  Individual Agent Files:                                  │       │
│  │  - requirements_agent.py    - pws_agent.py               │       │
│  │  - igce_agent.py            - scorecard_agent.py         │       │
│  │  - ssp_agent.py             - rfp_agent.py               │       │
│  │  - qa_agent.py              - refinement_agent.py        │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                              ▲  │
                              │  │ API Calls
                              │  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                                 │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Anthropic   │  │   OpenAI     │  │   Tavily     │              │
│  │  Claude API  │  │     API      │  │     API      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend
- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 5.4
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Fetch API
- **WebSocket**: Native WebSocket API

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Server**: Uvicorn with auto-reload
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT tokens with PBKDF2 password hashing
- **WebSocket**: FastAPI WebSocket support
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Database
- **Primary Database**: PostgreSQL 14+
- **Connection Pool**: SQLAlchemy connection pooling (20 connections, 10 overflow)

### AI Services
- **Primary**: Anthropic Claude (Sonnet 4.5)
- **Secondary**: OpenAI GPT-4
- **Research**: Tavily Search API

---

## Data Flow

### 1. User Authentication Flow

```
User enters credentials
    ↓
Frontend → POST /api/auth/login
    ↓
Backend validates credentials (PBKDF2 hash verification)
    ↓
Backend generates JWT token (30 min expiry)
    ↓
Token stored in localStorage
    ↓
All subsequent requests include: Authorization: Bearer <token>
```

### 2. Project Creation Flow

```
User fills project form
    ↓
Frontend → POST /api/projects
    ↓
Backend validates user role (contracting_officer or program_manager)
    ↓
Backend creates project in database
    ↓
Backend auto-creates 6 phases (pre_solicitation → closeout)
    ↓
Project data returned to frontend
    ↓
Frontend updates UI with new project
```

### 3. Document Generation Flow (AI Pipeline)

```
User clicks "Generate PWS" button
    ↓
Frontend → POST /api/projects/{id}/generate-document
    ↓
Backend starts async document generation
    ↓
WebSocket connection established: ws://localhost:8000/ws/{project_id}
    ↓
Backend calls AI agents in sequence:

    Phase 0: Requirements Analysis
    └→ Sends progress: {"type": "progress", "percentage": 20, "message": "Analyzing requirements..."}

    Phase 1: Pre-Solicitation
    └→ Sends progress: {"type": "progress", "percentage": 40, "message": "Generating PWS..."}

    Phase 2: Solicitation
    └→ Sends progress: {"type": "progress", "percentage": 60, "message": "Creating RFP..."}

    Phase 3: Refinement
    └→ Sends progress: {"type": "progress", "percentage": 80, "message": "Refining document..."}

    Completion:
    └→ Sends complete: {"type": "generation_complete", "document_url": "/files/pws_123.md"}
    ↓
Frontend receives updates via WebSocket
    ↓
Progress bar updates in real-time
    ↓
Document download link appears when complete
```

---

## Authentication Flow

### Registration
1. User submits registration form
2. Backend hashes password using PBKDF2-SHA256 (100,000 iterations)
3. User record created in database
4. User automatically logged in

### Login
1. User submits email/password
2. Backend retrieves user by email
3. Backend verifies password hash
4. Backend generates JWT token with user ID as subject
5. Token returned to frontend with user data
6. Token stored in localStorage

### Protected Routes
1. Frontend includes token in Authorization header
2. Backend extracts and verifies JWT token
3. Backend loads user from database using token subject
4. User object available in route handler
5. Role-based authorization checked if needed

### Token Structure
```json
{
  "sub": "user-uuid-here",
  "exp": 1762179072
}
```

---

## Document Generation Pipeline

### Step-by-Step Process

#### 1. **User Initiates Generation**
```typescript
// Frontend code
const handleGeneratePWS = async () => {
  await projectsApi.generateDocument(projectId, 'pws');
};
```

#### 2. **Backend Receives Request**
```python
# backend/main.py
@app.post("/api/projects/{project_id}/generate-document")
async def generate_document(project_id: str, document_type: str):
    # Start async generation
    asyncio.create_task(
        document_generator.generate_pws(project_id, project_data)
    )
    return {"message": "Generation started"}
```

#### 3. **AI Agent Execution**
```python
# backend/services/document_generator.py
async def generate_pws(self, project_id, requirements):
    # Send progress update via WebSocket
    await ws_manager.send_progress_update(
        project_id, "requirements", "Analyzing...", 20
    )

    # Call your AI agent
    result = await analyze_requirements(requirements)

    # Continue with next phase...
    await ws_manager.send_progress_update(
        project_id, "pre_solicitation", "Generating PWS...", 50
    )

    pws_content = await generate_pws(result)

    # Save and complete
    file_path = save_document(pws_content, project_id)
    await ws_manager.send_generation_complete(
        project_id, "PWS", f"/files/{file_path}"
    )
```

#### 4. **Real-time Updates to Frontend**
```typescript
// Frontend WebSocket hook
const { progress, message, status, documentUrl } = useDocumentGeneration(projectId);

// UI updates automatically as progress changes
<ProgressBar value={progress} />
<p>{message}</p>
{status === 'complete' && <DownloadButton url={documentUrl} />}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,  -- contracting_officer, program_manager, approver, viewer
    department VARCHAR(255),
    notification_preferences JSONB DEFAULT '{"email": true, "in_app": true, "deadline_days": [1,3,7]}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Procurement Projects Table
```sql
CREATE TABLE procurement_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) NOT NULL,  -- rfp, rfq, rfi, bpa, idiq
    estimated_value NUMERIC(15, 2),
    contracting_officer_id UUID REFERENCES users(id),
    program_manager_id UUID REFERENCES users(id),
    current_phase VARCHAR(50) DEFAULT 'pre_solicitation',
    overall_status VARCHAR(50) DEFAULT 'not_started',
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Procurement Phases Table
```sql
CREATE TABLE procurement_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES procurement_projects(id) ON DELETE CASCADE,
    phase_name VARCHAR(50) NOT NULL,
    phase_order INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started',
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    completion_percentage INTEGER DEFAULT 0,
    estimated_duration_days INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Project Documents Table
```sql
CREATE TABLE project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES procurement_projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES procurement_phases(id),
    document_name VARCHAR(500) NOT NULL,
    document_type VARCHAR(100),
    file_path TEXT,
    file_url TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    file_size BIGINT,
    mime_type VARCHAR(100)
);
```

---

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user.

**Request:**
```json
{
  "email": "john.doe@navy.mil",
  "password": "secure_password",
  "name": "John Doe",
  "role": "contracting_officer"
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "uuid",
    "email": "john.doe@navy.mil",
    "name": "John Doe",
    "role": "contracting_officer"
  }
}
```

#### POST /api/auth/login
Login and receive JWT token.

**Request:**
```json
{
  "email": "john.doe@navy.mil",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { /* user object */ }
}
```

#### GET /api/auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "john.doe@navy.mil",
  "name": "John Doe",
  "role": "contracting_officer"
}
```

### Project Endpoints

#### GET /api/projects
List all projects (with authorization filtering).

**Response:**
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Advanced Navy Training System",
      "description": "...",
      "project_type": "rfp",
      "estimated_value": 25000000.0,
      "current_phase": "pre_solicitation",
      "overall_status": "in_progress"
    }
  ]
}
```

#### POST /api/projects
Create a new project.

**Request:**
```json
{
  "name": "New Procurement Project",
  "description": "Project description",
  "project_type": "rfp",
  "estimated_value": 10000000.0
}
```

#### GET /api/projects/{id}/phases
Get all phases for a project.

**Response:**
```json
{
  "phases": [
    {
      "id": "uuid",
      "phase_name": "pre_solicitation",
      "status": "in_progress",
      "completion_percentage": 45
    }
  ]
}
```

#### POST /api/projects/{id}/generate-document
Generate AI document for project.

**Request:**
```json
{
  "document_type": "pws"  // or "igce", "rfp", "scorecard", etc.
}
```

**Response:**
```json
{
  "message": "Document generation started",
  "task_id": "task-uuid"
}
```

### WebSocket Endpoint

#### WS /ws/{project_id}
Real-time updates for document generation.

**Messages Received:**
```json
// Progress update
{
  "type": "progress",
  "percentage": 45,
  "message": "Generating PWS section 3..."
}

// Completion
{
  "type": "generation_complete",
  "document_type": "PWS",
  "document_url": "/files/pws_123.md"
}

// Error
{
  "type": "error",
  "message": "Failed to generate document"
}
```

---

## Frontend Architecture

### Directory Structure
```
dod_contracting_front_end/
├── src/
│   ├── components/
│   │   ├── procurement/
│   │   │   ├── ProcurementHub.tsx         # Main tracker UI
│   │   │   ├── SegmentedTrackerBar.tsx    # Progress bar
│   │   │   └── ProjectCard.tsx
│   │   ├── ai-studio/
│   │   │   └── AIStudio.tsx               # AI document generation UI
│   │   └── dashboard/
│   │       └── Dashboard.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx                 # Authentication state
│   ├── hooks/
│   │   ├── useProcurementProjects.ts      # Project data management
│   │   ├── useDocumentGeneration.ts       # WebSocket hook
│   │   └── useAuth.ts
│   ├── services/
│   │   └── api.ts                          # API service layer
│   ├── lib/
│   │   └── utils.ts
│   └── App.tsx
└── .env.local                              # Environment config
```

### Key Components

#### 1. **API Service Layer** (`src/services/api.ts`)
Centralizes all backend communication.

```typescript
// Authentication
authApi.login(email, password)
authApi.register(email, password, name, role)
authApi.me()

// Projects
projectsApi.list()
projectsApi.create(projectData)
projectsApi.generateDocument(id, type)

// WebSocket
createWebSocket(projectId)
```

#### 2. **Authentication Context** (`src/contexts/AuthContext.tsx`)
Manages user state and authentication.

```typescript
const { user, loading, signIn, signOut, hasRole } = useAuth();
```

#### 3. **WebSocket Hook** (`src/hooks/useDocumentGeneration.ts`)
Handles real-time updates.

```typescript
const { progress, message, status, documentUrl } = useDocumentGeneration(projectId);
```

#### 4. **Project Management Hook** (`src/hooks/useProcurementProjects.ts`)
CRUD operations for projects.

```typescript
const { projects, loading, createProject, updateProject } = useProcurementProjects();
```

---

## Deployment Guide

### Local Development

#### 1. Start PostgreSQL
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Create database
createdb dod_procurement
```

#### 2. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
python backend/main.py
```

Backend runs at: http://localhost:8000
API Docs at: http://localhost:8000/docs

#### 3. Start Frontend
```bash
cd dod_contracting_front_end
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

### Production Deployment

#### Option 1: Docker Compose
```yaml
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: dod_procurement
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/dod_procurement
    depends_on:
      - db

  frontend:
    build: ./dod_contracting_front_end
    ports:
      - "80:80"
    depends_on:
      - backend
```

#### Option 2: Cloud Deployment
- **Backend**: Deploy to AWS ECS, Google Cloud Run, or Railway
- **Frontend**: Deploy to Vercel, Netlify, or AWS S3 + CloudFront
- **Database**: Use AWS RDS, Google Cloud SQL, or Supabase PostgreSQL

---

## Security Considerations

### 1. **Password Security**
- Passwords hashed using PBKDF2-SHA256 with 100,000 iterations
- Unique salt per user
- Passwords never stored in plaintext

### 2. **JWT Tokens**
- Tokens expire after 30 minutes
- Stored in localStorage (consider httpOnly cookies for production)
- Include user ID only (no sensitive data)

### 3. **API Security**
- CORS configured for specific origins only
- All authenticated endpoints require valid JWT
- Role-based authorization enforced

### 4. **Input Validation**
- SQLAlchemy ORM prevents SQL injection
- Pydantic models validate all input data
- File uploads restricted by size and type

---

## Future Enhancements

1. **Redis Caching**: Cache frequently accessed data
2. **Celery Background Tasks**: Offload long-running AI generation
3. **Email Notifications**: Alert users on document completion
4. **File Upload**: Support requirement document uploads
5. **Audit Logging**: Track all user actions
6. **Advanced Search**: Full-text search across projects and documents
7. **Export Functionality**: Export projects to PDF/Excel
8. **Collaborative Editing**: Real-time collaboration on documents

---

## Support & Contact

For technical questions or issues:
- Review API documentation: http://localhost:8000/docs
- Check logs: `backend/logs/api.log`
- Database queries: `psql -d dod_procurement`

---

**Last Updated**: November 2025
**Version**: 1.0.0
