# DoD Procurement Document Generation API

Python-based FastAPI backend for AI-powered DoD procurement document generation system.

## Architecture

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
│
├── api/                   # API route handlers (future expansion)
├── models/                # SQLAlchemy ORM models
│   ├── user.py           # User and authentication
│   ├── procurement.py    # Project, phase, step models
│   ├── document.py       # Document management
│   ├── notification.py   # Notifications
│   └── audit.py          # Audit logging
│
├── services/             # Business logic services
│   ├── websocket_manager.py    # Real-time WebSocket handling
│   └── document_generator.py   # AI document generation
│
├── middleware/           # Middleware components
│   └── auth.py          # JWT authentication
│
├── database/            # Database configuration
│   └── base.py         # SQLAlchemy setup
│
├── schemas/            # Pydantic schemas (future)
├── utils/              # Utility functions
└── scripts/            # Utility scripts
    └── seed_database.py  # Database seeding
```

## Features

- ✅ **RESTful API** - Complete CRUD operations for projects, documents, users
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **Role-Based Access Control** - Four user roles (CO, PM, Approver, Viewer)
- ✅ **Real-time WebSocket** - Live progress updates during document generation
- ✅ **PostgreSQL Database** - Production-ready relational database
- ✅ **Document Management** - Full lifecycle tracking with approval workflows
- ✅ **AI Integration Ready** - Connects to your existing document generation scripts

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Database

Install PostgreSQL if not already installed:

```bash
# macOS
brew install postgresql
brew services start postgresql

# Create database
createdb dod_procurement
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dod_procurement
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
```

### 4. Initialize and Seed Database

```bash
# Seed database with sample data
python -m backend.scripts.seed_database
```

### 5. Run the Server

```bash
# Development mode (auto-reload)
python backend/main.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Test Users

After seeding the database, you can login with:

| Email | Password | Role |
|-------|----------|------|
| john.contracting@navy.mil | password123 | Contracting Officer |
| sarah.pm@navy.mil | password123 | Program Manager |
| mike.approver@navy.mil | password123 | Approver |
| viewer@navy.mil | password123 | Viewer |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Projects
- `GET /api/projects` - List all accessible projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects/{id}/phases` - Get project phases
- `GET /api/projects/{id}/documents` - Get project documents

### Document Generation
- `POST /api/projects/{id}/generate-document` - Trigger AI document generation

### Notifications
- `GET /api/notifications` - Get user notifications
- `PATCH /api/notifications/{id}/read` - Mark notification as read

### WebSocket
- `WS /ws/{project_id}` - Real-time updates for project

## Using the API

### 1. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john.contracting@navy.mil", "password": "password123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {...}
}
```

### 2. Create a Project

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Training System RFP",
    "description": "Procurement for advanced training system",
    "project_type": "rfp",
    "estimated_value": 10000000
  }'
```

### 3. Generate Documents

```bash
curl -X POST http://localhost:8000/api/projects/{PROJECT_ID}/generate-document \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type": application/json" \
  -d '{"document_type": "pws"}'
```

### 4. WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/PROJECT_ID');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'progress') {
    console.log(`Progress: ${data.percentage}% - ${data.message}`);
  }

  if (data.type === 'generation_complete') {
    console.log(`Document ready: ${data.document_url}`);
  }
};
```

## Integrating Your Existing Code

The backend is designed to integrate with your existing document generation scripts:

### 1. Link Your Scripts

Your existing code in `scripts/generate_all_phases_alms.py` can be called from the API:

```python
# backend/services/document_generator.py

from scripts.generate_all_phases_alms import (
    generate_phase0_requirements,
    generate_phase1_pws,
    generate_phase2_rfp,
    generate_phase3_award
)

async def generate_pws(self, project_id: str, requirements: str):
    # Call your existing function
    result = await self._run_in_thread(
        generate_phase1_pws,
        requirements
    )

    # Send progress updates
    await ws_manager.send_progress_update(
        project_id,
        "pre_solicitation",
        "PWS generated successfully",
        100
    )

    return result
```

### 2. Progress Updates

Add progress callbacks to your existing agents:

```python
# In your existing agent code
async def generate_document(requirements, progress_callback=None):
    if progress_callback:
        await progress_callback("Analyzing requirements...", 10)

    # ... your existing logic ...

    if progress_callback:
        await progress_callback("Generating document...", 50)

    # ... more logic ...
```

## Database Schema

The backend uses the same schema as the front-end (matching Supabase design):

- **users** - User accounts and roles
- **procurement_projects** - Main project tracking
- **procurement_phases** - 3 phases per project
- **procurement_steps** - Individual workflow steps
- **project_documents** - Document checklist
- **document_uploads** - File version tracking
- **document_approvals** - Approval workflows
- **notifications** - User notifications
- **audit_log** - Change tracking

## Next Steps

1. **Connect Front-End**: Update the React app to call this API instead of Supabase
2. **Integrate AI Agents**: Wire up your existing document generation code
3. **Add File Upload**: Implement file upload endpoints
4. **Add Celery**: For long-running background tasks
5. **Add Redis**: For caching and task queue
6. **Deploy**: Set up production deployment (Docker, AWS, etc.)

## Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```env
DATABASE_URL=postgresql://user:pass@prod-db:5432/dod_procurement
SECRET_KEY=STRONG-RANDOM-SECRET-KEY
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
CORS_ORIGINS=https://yourdomain.com
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep dod_procurement

# Reset database
dropdb dod_procurement
createdb dod_procurement
python -m backend.scripts.seed_database
```

### Import Errors

Make sure you're running from the project root:

```bash
# From project root
python backend/main.py

# NOT from backend directory
cd backend && python main.py  # This won't work
```

## Support

For issues or questions:
1. Check the API docs at http://localhost:8000/docs
2. Review the code in `backend/main.py`
3. Check logs for error messages
