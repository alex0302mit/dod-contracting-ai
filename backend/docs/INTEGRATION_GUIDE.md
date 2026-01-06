# DoD Procurement System - Full Stack Integration Guide

Complete guide to connect your Python backend with the React front-end.

## Overview

This guide walks you through integrating:
- ✅ **Backend**: Python FastAPI with your existing AI document generation
- ✅ **Frontend**: React/TypeScript UI
- ✅ **Database**: PostgreSQL (replacing Supabase)
- ✅ **Real-time**: WebSockets for live updates

## Step-by-Step Integration

### Phase 1: Backend Setup (30 minutes)

#### 1.1 Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 1.2 Set Up PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or: sudo apt-get install postgresql  # Linux

# Start PostgreSQL
brew services start postgresql  # macOS
# or: sudo systemctl start postgresql  # Linux

# Create database
createdb dod_procurement
```

#### 1.3 Configure Environment

```bash
cp backend/.env.example backend/.env #I am here
```

Edit `backend/.env`:
```env
DATABASE_URL=https://rgipvcvznxftjqmyqtmw.supabase.co
SECRET_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJnaXB2Y3Z6bnhmdGpxbXlxdG13Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MjQ0MjQsImV4cCI6MjA3NzQwMDQyNH0.z5KFkyVbVe0SgKhSIUL9IhbxpYVAKqFCIm7NaBQVVPI

ANTHROPIC_API_KEY=your-existing-key
OPENAI_API_KEY=your-existing-key
CORS_ORIGINS=http://localhost:5173
```

#### 1.4 Initialize Database

```bash
python -m backend.scripts.seed_database
```

#### 1.5 Start Backend Server

```bash
python backend/main.py
```

Verify at: http://localhost:8000/docs

---

### Phase 2: Integrate Your AI Agents (45 minutes)

#### 2.1 Link Existing Scripts

Your existing `scripts/generate_all_phases_alms.py` needs minimal changes:

**Current structure:**
```
scripts/
├── generate_all_phases_alms.py
├── agents/
│   ├── requirements_agent.py
│   ├── pws_agent.py
│   └── ...
```

**Update `backend/services/document_generator.py`:**

```python
# Add imports for your existing code
import sys
from pathlib import Path

# Import your existing agents
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.agents.requirements_agent import analyze_requirements
from scripts.agents.pws_agent import generate_pws
from scripts.agents.refinement_agent import refine_document

class DocumentGeneratorService:
    async def generate_pws(self, project_id, requirements):
        # Phase 1: Requirements analysis
        await ws_manager.send_progress_update(
            project_id,
            "requirements",
            "Analyzing requirements...",
            20
        )

        # Call YOUR existing function
        phase0_result = await self._run_in_thread(
            analyze_requirements,
            requirements
        )

        # Phase 2: PWS generation
        await ws_manager.send_progress_update(
            project_id,
            "pre_solicitation",
            "Generating PWS...",
            50
        )

        # Call YOUR existing function
        pws_content = await self._run_in_thread(
            generate_pws,
            phase0_result
        )

        # Phase 3: Refinement
        await ws_manager.send_progress_update(
            project_id,
            "pre_solicitation",
            "Refining document...",
            80
        )

        # Call YOUR existing function
        refined_pws = await self._run_in_thread(
            refine_document,
            pws_content
        )

        # Save to file
        output_path = self.save_document(refined_pws, project_id, "pws")

        # Complete
        await ws_manager.send_generation_complete(
            project_id,
            "PWS",
            f"/files/{output_path.name}"
        )

        return {"file_path": str(output_path)}
```

#### 2.2 Update Main API Endpoint

Edit `backend/main.py`:

```python
from backend.services.document_generator import document_generator

@app.post("/api/projects/{project_id}/generate-document")
async def generate_document(
    project_id: str,
    document_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI document"""
    project = db.query(ProcurementProject).filter(
        ProcurementProject.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Call your integrated service
    if document_type == "pws":
        result = await document_generator.generate_pws(
            project_id,
            project.name,
            project.description,
            project.project_type
        )
    elif document_type == "all":
        result = await document_generator.generate_all_phases(
            project_id,
            project.to_dict()
        )

    # Save result to database
    doc = ProjectDocument(
        project_id=project_id,
        document_name=f"Generated {document_type.upper()}",
        status="uploaded",
        file_path=result["file_path"]
    )
    db.add(doc)
    db.commit()

    return result
```

---

### Phase 3: Frontend Integration (45 minutes)

#### 3.1 Create API Service Layer

Create `dod_contracting_front_end/src/services/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token from storage
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

// API client with authentication
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

// Projects API
export const projectsApi = {
  list: () => apiRequest('/api/projects'),

  get: (id: string) => apiRequest(`/api/projects/${id}`),

  create: (data: any) =>
    apiRequest('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getPhases: (id: string) => apiRequest(`/api/projects/${id}/phases`),

  getDocuments: (id: string) => apiRequest(`/api/projects/${id}/documents`),

  generateDocument: (id: string, documentType: string) =>
    apiRequest(`/api/projects/${id}/generate-document`, {
      method: 'POST',
      body: JSON.stringify({ document_type: documentType }),
    }),
};

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, name: string, role: string) =>
    apiRequest('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, role }),
    }),

  me: () => apiRequest('/api/auth/me'),
};
```

#### 3.2 Update Environment Variables

Create `dod_contracting_front_end/.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

#### 3.3 Replace Supabase Calls

Update `dod_contracting_front_end/src/hooks/useProcurementProjects.ts`:

**Before (Supabase):**
```typescript
const { data: projects } = await supabase
  .from('procurement_projects')
  .select('*');
```

**After (Python API):**
```typescript
import { projectsApi } from '@/services/api';

export function useProcurementProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const data = await projectsApi.list();
        setProjects(data.projects);
      } catch (error) {
        console.error('Error fetching projects:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
  }, []);

  return { projects, loading };
}
```

#### 3.4 Add WebSocket Hook

Create `dod_contracting_front_end/src/hooks/useDocumentGeneration.ts`:

```typescript
import { useEffect, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useDocumentGeneration(projectId: string) {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/${projectId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'generation_started':
          setStatus('generating');
          setProgress(0);
          setMessage('Starting document generation...');
          break;

        case 'progress':
          setProgress(data.percentage);
          setMessage(data.message);
          break;

        case 'generation_complete':
          setStatus('complete');
          setProgress(100);
          setMessage('Document generated successfully!');
          setDocumentUrl(data.document_url);
          break;

        case 'error':
          setStatus('error');
          setMessage(data.message);
          break;
      }
    };

    ws.onerror = () => {
      setStatus('error');
      setMessage('Connection error');
    };

    return () => ws.close();
  }, [projectId]);

  return { progress, message, status, documentUrl };
}
```

#### 3.5 Update AuthContext

Replace `dod_contracting_front_end/src/contexts/AuthContext.tsx` to use your API:

```typescript
import { authApi } from '@/services/api';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      authApi.me()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('auth_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const signIn = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    localStorage.setItem('auth_token', response.access_token);
    setUser(response.user);
  };

  const signOut = async () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
```

---

### Phase 4: Testing the Integration (15 minutes)

#### 4.1 Start Both Servers

Terminal 1 - Backend:
```bash
cd backend
python main.py
```

Terminal 2 - Frontend:
```bash
cd dod_contracting_front_end
npm run dev
```

#### 4.2 Test Login

1. Open http://localhost:5173
2. Login with test credentials:
   - Email: `john.contracting@navy.mil`
   - Password: `password123`

#### 4.3 Test Document Generation

1. Navigate to "Tracker"
2. Click on "Advanced Navy Training System (ANTS)" project
3. Click "Generate PWS" button
4. Watch real-time progress bar update via WebSocket
5. Download generated document when complete

---

### Phase 5: Production Deployment

#### 5.1 Backend Deployment (Docker)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 5.2 Frontend Build

```bash
cd dod_contracting_front_end
npm run build
```

Deploy `dist/` folder to your hosting service (Vercel, Netlify, AWS S3, etc.)

---

## Common Issues & Solutions

### Issue: CORS Error

**Solution**: Update `backend/main.py`:
```python
CORS_ORIGINS = ["http://localhost:5173", "https://yourdomain.com"]
```

### Issue: WebSocket Connection Fails

**Solution**: Check firewall settings and ensure WebSocket protocol is allowed.

### Issue: Database Connection Error

**Solution**: Verify PostgreSQL is running and credentials are correct:
```bash
psql -U YOUR_USER -d dod_procurement -c "SELECT 1"
```

### Issue: Import Errors

**Solution**: Run from project root, not from `backend/` directory:
```bash
# Correct
python backend/main.py

# Incorrect
cd backend && python main.py
```

---

## Performance Optimization

### Add Redis Caching

```bash
brew install redis
brew services start redis
```

Update `backend/main.py`:
```python
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

@app.get("/api/projects")
def get_projects():
    # Try cache first
    cached = redis_client.get("projects_list")
    if cached:
        return json.loads(cached)

    # Fetch from DB
    projects = db.query(ProcurementProject).all()
    result = {"projects": [p.to_dict() for p in projects]}

    # Cache for 5 minutes
    redis_client.setex("projects_list", 300, json.dumps(result))

    return result
```

### Add Celery for Background Tasks

```python
from celery import Celery

celery_app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))

@celery_app.task
def generate_document_task(project_id, document_type):
    # Long-running document generation
    result = document_generator.generate_pws(project_id, ...)
    return result

@app.post("/api/projects/{project_id}/generate-document")
async def generate_document(project_id: str):
    # Queue task instead of running immediately
    task = generate_document_task.delay(project_id, "pws")
    return {"task_id": task.id, "status": "queued"}
```

---

## Next Steps

1. ✅ Complete backend-frontend integration
2. ✅ Test all workflows end-to-end
3. ⬜ Add file upload functionality
4. ⬜ Implement email notifications
5. ⬜ Add comprehensive error handling
6. ⬜ Set up CI/CD pipeline
7. ⬜ Deploy to production
8. ⬜ Add monitoring and logging (Sentry, DataDog, etc.)

---

## Support & Resources

- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Backend Code**: `backend/main.py`
- **Frontend Code**: `dod_contracting_front_end/src/`

For questions or issues, review the code comments or check the logs.
