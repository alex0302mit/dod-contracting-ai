# 🚀 Startup Scripts Guide

## Quick Start

### Start Everything (Recommended)
```bash
./start_all.sh
```
This starts both backend and frontend in a split terminal (using tmux if available).

### Start Individually

**Backend only:**
```bash
./start_backend.sh
```

**Frontend only:**
```bash
./start_frontend.sh
```

### Stop Everything
```bash
./stop_all.sh
```

---

## 📋 What Each Script Does

### `start_backend.sh`
- ✅ Checks Python version
- ✅ Creates/activates virtual environment
- ✅ Installs dependencies (if needed)
- ✅ Checks environment variables
- ✅ Initializes database
- ✅ Seeds test users (if database is empty)
- ✅ Starts FastAPI server on http://localhost:8000

### `start_frontend.sh`
- ✅ Checks Node.js/npm versions
- ✅ Installs dependencies (if needed)
- ✅ Checks backend connection
- ✅ Starts Vite dev server on http://localhost:5173

### `start_all.sh`
- ✅ Uses tmux or screen for split terminal
- ✅ Starts backend in one pane
- ✅ Starts frontend in another pane
- ✅ Falls back to background mode if tmux/screen not available

### `stop_all.sh`
- ✅ Stops tmux/screen sessions
- ✅ Kills backend processes
- ✅ Kills frontend processes

---

## 🔐 Test Login Credentials

After starting, login with:

| Email | Password | Role |
|-------|----------|------|
| `john.contracting@navy.mil` | `password123` | Contracting Officer |
| `sarah.pm@navy.mil` | `password123` | Program Manager |
| `mike.approver@navy.mil` | `password123` | Approver |
| `viewer@navy.mil` | `password123` | Viewer |

---

## 🌐 URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🛠️ Troubleshooting

### "Permission denied" error
```bash
chmod +x *.sh
```

### Backend won't start
- Check if port 8000 is in use: `lsof -i :8000`
- Kill existing process: `pkill -f "python.*backend/main.py"`

### Frontend won't start
- Check if port 5173 is in use: `lsof -i :5173`
- Kill existing process: `pkill -f vite`

### Dependencies not installing
```bash
# Backend
rm backend/venv/.deps_installed
./start_backend.sh

# Frontend
cd dod_contracting_front_end && rm -rf node_modules && npm install
```

### Reset database
```bash
rm dod_procurement.db
./start_backend.sh
```

---

## 🎓 Using tmux (if installed)

When using `start_all.sh` with tmux:

- **Detach** from session: `Ctrl+B` then `D`
- **Re-attach**: `tmux attach -t dod_contracting`
- **Switch panes**: `Ctrl+B` then arrow keys
- **Kill session**: `tmux kill-session -t dod_contracting`

---

## 📝 Environment Variables

Optional environment variables you can set:

```bash
# AI API Key (required for AI features)
export ANTHROPIC_API_KEY='your-key-here'

# Backend configuration
export API_HOST='0.0.0.0'
export API_PORT=8000
export API_RELOAD='true'

# CORS origins
export CORS_ORIGINS='http://localhost:5173,http://localhost:3000'
```

---

## 🔧 Advanced Usage

### Reinstall all dependencies
```bash
# Backend
rm backend/venv/.deps_installed
rm -rf backend/venv
./start_backend.sh

# Frontend
cd dod_contracting_front_end
rm -rf node_modules package-lock.json
npm install
```

### Run in production mode
```bash
export API_RELOAD='false'
./start_backend.sh
```

### View logs
```bash
# If using start_all.sh without tmux
tail -f backend.log
```

---

## ✨ First Time Setup

1. **Set your API key** (optional, for AI features):
   ```bash
   export ANTHROPIC_API_KEY='your-key-here'
   ```

2. **Start everything**:
   ```bash
   ./start_all.sh
   ```

3. **Open your browser**:
   - Frontend: http://localhost:5173
   - Login with: `john.contracting@navy.mil` / `password123`

That's it! 🎉

