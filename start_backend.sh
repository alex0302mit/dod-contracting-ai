#!/bin/bash

# DoD Contracting Backend Startup Script
# This script handles all backend initialization and startup
# Includes optional Celery worker for distributed task processing

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track background processes for cleanup
CELERY_PID=""

# Cleanup function to stop background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"

    if [ -n "$CELERY_PID" ] && kill -0 "$CELERY_PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Celery worker (PID: $CELERY_PID)...${NC}"
        kill -TERM "$CELERY_PID" 2>/dev/null || true
        # Wait up to 10 seconds for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$CELERY_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 "$CELERY_PID" 2>/dev/null; then
            kill -9 "$CELERY_PID" 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ Celery worker stopped${NC}"
    fi

    echo -e "${GREEN}✓ Shutdown complete${NC}"
    exit 0
}

# Set up trap to catch SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DoD Contracting Backend Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Step 2: Check/Activate virtual environment
echo -e "${YELLOW}[2/7] Setting up virtual environment...${NC}"
if [ ! -d "apps/api/venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv apps/api/venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source apps/api/venv/bin/activate

# Set PYTHONPATH so Python can find the backend module (now at apps/api)
# We add both the root and apps/api so imports work with 'backend.' prefix
export PYTHONPATH="${SCRIPT_DIR}/apps/api:${SCRIPT_DIR}:${PYTHONPATH}"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 3: Install/Update dependencies
echo -e "${YELLOW}[3/7] Checking dependencies...${NC}"
if [ ! -f "apps/api/venv/.deps_installed" ]; then
    echo "   Installing dependencies (this may take a few minutes)..."
    pip install -q --upgrade pip
    pip install -q -r apps/api/requirements.txt
    touch apps/api/venv/.deps_installed
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed (use --reinstall to update)${NC}"
fi
echo ""

# Step 4: Check environment variables
echo -e "${YELLOW}[4/7] Checking environment variables...${NC}"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY not set${NC}"
    echo "   Set it with: export ANTHROPIC_API_KEY=your api key"
    echo "   (AI features will not work without this)"
else
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY is set${NC}"
fi

# Set default environment variables if not set
export API_HOST=${API_HOST:-"0.0.0.0"}
export API_PORT=${API_PORT:-8000}
# Reload disabled by default to avoid venv file watcher issues
# Set API_RELOAD=true before running this script to enable hot reload
export API_RELOAD=${API_RELOAD:-"false"}
export CORS_ORIGINS=${CORS_ORIGINS:-"http://localhost:5173,http://localhost:5174,http://localhost:3000"}
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Check Redis status (optional - for caching and Celery)
echo -e "${YELLOW}Checking optional services...${NC}"
if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓ Redis is running (caching & task queue enabled)${NC}"
    export REDIS_CACHE_ENABLED=true
    export USE_CELERY_TASKS=true
    REDIS_AVAILABLE=true
else
    echo -e "${YELLOW}⚠  Redis not running (caching & Celery disabled - app will still work)${NC}"
    echo "   To enable Redis: brew install redis && brew services start redis"
    export REDIS_CACHE_ENABLED=false
    export USE_CELERY_TASKS=false
    REDIS_AVAILABLE=false
fi
echo ""

# Step 5: Initialize database
echo -e "${YELLOW}[5/7] Initializing database...${NC}"
if [ ! -f "dod_procurement.db" ]; then
    echo "   Creating new database..."
    python3 -c "from backend.database.base import init_db; init_db()"
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${GREEN}✓ Database exists${NC}"
fi
echo ""

# Step 6: Check if database needs seeding
echo -e "${YELLOW}[6/7] Checking database users...${NC}"
USER_COUNT=$(python3 -c "
from backend.database.base import SessionLocal
from backend.models.user import User
db = SessionLocal()
count = db.query(User).count()
db.close()
print(count)
" 2>/dev/null || echo "0")

if [ "$USER_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}   No users found. Seeding database...${NC}"
    python3 tools/setup/seed_database.py
    echo -e "${GREEN}✓ Database seeded with test users${NC}"
    echo ""
    echo -e "${BLUE}📧 Test Login Credentials:${NC}"
    echo "   Email: john.contracting@navy.mil"
    echo "   Password: password123"
else
    echo -e "${GREEN}✓ Database has $USER_COUNT user(s)${NC}"
fi
echo ""

# Start Celery worker if Redis is available
if [ "$REDIS_AVAILABLE" = "true" ]; then
    echo -e "${YELLOW}[7/7] Starting Celery worker...${NC}"

    # Detect OS for Celery pool configuration
    # macOS requires solo pool because PyTorch/SentenceTransformer are not fork-safe
    # Linux can use prefork pool for better performance with multiple workers
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CELERY_POOL="solo"
        echo -e "${YELLOW}   Detected macOS - using solo pool (fork-safe for PyTorch)${NC}"
    else
        CELERY_POOL="prefork"
        CELERY_WORKERS=4
        echo -e "${GREEN}   Detected Linux - using prefork pool with ${CELERY_WORKERS} workers${NC}"
    fi

    # Start Celery worker in background with output logging
    # Pool configuration differs between macOS (solo) and Linux (prefork)
    if [ "$CELERY_POOL" = "solo" ]; then
        # Solo pool: single worker, no concurrency flag (processes tasks sequentially)
        celery -A backend.celery_app worker \
            --loglevel=info \
            --pool=solo \
            --queues=dod.generation.high,dod.generation.batch,dod.quality,celery \
            --hostname=worker@%h \
            > celery_worker.log 2>&1 &
    else
        # Prefork pool: multiple workers for parallel task processing
        celery -A backend.celery_app worker \
            --loglevel=info \
            --pool=prefork \
            --concurrency=$CELERY_WORKERS \
            --queues=dod.generation.high,dod.generation.batch,dod.quality,celery \
            --hostname=worker@%h \
            > celery_worker.log 2>&1 &
    fi

    CELERY_PID=$!

    # Wait a moment and check if worker started
    sleep 2
    if kill -0 "$CELERY_PID" 2>/dev/null; then
        echo -e "${GREEN}✓ Celery worker started (PID: $CELERY_PID, pool: $CELERY_POOL)${NC}"
        echo "   Logs: tail -f celery_worker.log"
    else
        echo -e "${YELLOW}⚠  Celery worker failed to start (check celery_worker.log)${NC}"
        CELERY_PID=""
    fi
    echo ""
fi

# Start the server
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Backend Server...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}API Server:${NC} http://localhost:$API_PORT"
echo -e "${GREEN}API Docs:${NC} http://localhost:$API_PORT/docs"
echo -e "${GREEN}Health Check:${NC} http://localhost:$API_PORT/health"
if [ "$REDIS_CACHE_ENABLED" = "true" ]; then
    echo -e "${GREEN}Cache Stats:${NC} http://localhost:$API_PORT/api/cache/stats"
fi
if [ -n "$CELERY_PID" ]; then
    echo -e "${GREEN}Celery Worker:${NC} Running (PID: $CELERY_PID)"
    echo -e "${GREEN}Celery Logs:${NC} tail -f celery_worker.log"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Start the server (this blocks until Ctrl+C)
python3 apps/api/main.py

