# Backend Quick Start - 10 Minutes to Running System

## Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (for frontend)

## Step 1: Backend Setup (5 minutes)

```bash
# Navigate to project root
cd "/Users/alejandromaldonado/Desktop/AI_Phantom_Fellow_Course/Basic use case market research LLM automation"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Create PostgreSQL database
createdb dod_procurement

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and database credentials

# Seed database with test data
cd ..
python -m backend.scripts.seed_database

# Start backend server
python backend/main.py
```

Backend now running at **http://localhost:8000**

API Docs at **http://localhost:8000/docs**

## Step 2: Test the Backend

### 1. View API Docs
Go to **http://localhost:8000/docs**

### 2. Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john.contracting@navy.mil", "password": "password123"}'
```

You'll get a JWT token - copy it!

### 3. Test Get Projects
```bash
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

You should see the sample project!

## Test Credentials

| Email | Password | Role |
|-------|----------|------|
| john.contracting@navy.mil | password123 | Contracting Officer |
| sarah.pm@navy.mil | password123 | Program Manager |
| mike.approver@navy.mil | password123 | Approver |
| viewer@navy.mil | password123 | Viewer |

## Common Issues

### "Database connection failed"
```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL if needed
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux
```

### "Port already in use"
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### "Module not found"
```bash
# Run from project root, not from backend/
cd ..
python backend/main.py
```

## What's Working

✅ User authentication with JWT
✅ Project creation and management
✅ Phase tracking (3 phases)
✅ Document checklist
✅ Role-based access control
✅ Real-time WebSocket connections
✅ Sample data pre-loaded

## Next Steps

1. Read `BACKEND_SUMMARY.md` for complete overview
2. Read `INTEGRATION_GUIDE.md` for frontend integration
3. Read `ARCHITECTURE.md` for system design
4. Integrate your AI agents

## Key URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

Your backend is ready! Now integrate your AI agents and connect the frontend.
