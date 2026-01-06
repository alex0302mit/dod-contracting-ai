#!/bin/bash

# DoD Contracting Backend Startup Script
# This script handles all backend initialization and startup

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DoD Contracting Backend Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Step 2: Check/Activate virtual environment
echo -e "${YELLOW}[2/6] Setting up virtual environment...${NC}"
if [ ! -d "backend/venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv backend/venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source backend/venv/bin/activate

# Set PYTHONPATH so Python can find the backend module
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 3: Install/Update dependencies
echo -e "${YELLOW}[3/6] Checking dependencies...${NC}"
if [ ! -f "backend/venv/.deps_installed" ]; then
    echo "   Installing dependencies (this may take a few minutes)..."
    pip install -q --upgrade pip
    pip install -q -r backend/requirements.txt
    touch backend/venv/.deps_installed
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed (use --reinstall to update)${NC}"
fi
echo ""

# Step 4: Check environment variables
echo -e "${YELLOW}[4/6] Checking environment variables...${NC}"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY not set${NC}"
    echo "   Set it with: export ANTHROPIC_API_KEY='your-key-here'"
    echo "   (AI features will not work without this)"
else
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY is set${NC}"
fi

# Set default environment variables if not set
export API_HOST=${API_HOST:-"0.0.0.0"}
export API_PORT=${API_PORT:-8000}
export API_RELOAD=${API_RELOAD:-"true"}
export CORS_ORIGINS=${CORS_ORIGINS:-"http://localhost:5173,http://localhost:5174,http://localhost:3000"}
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Step 5: Initialize database
echo -e "${YELLOW}[5/6] Initializing database...${NC}"
if [ ! -f "dod_procurement.db" ]; then
    echo "   Creating new database..."
    python3 -c "from backend.database.base import init_db; init_db()"
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${GREEN}✓ Database exists${NC}"
fi
echo ""

# Step 6: Check if database needs seeding
echo -e "${YELLOW}[6/6] Checking database users...${NC}"
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
    python3 backend/scripts/seed_database.py
    echo -e "${GREEN}✓ Database seeded with test users${NC}"
    echo ""
    echo -e "${BLUE}📧 Test Login Credentials:${NC}"
    echo "   Email: john.contracting@navy.mil"
    echo "   Password: password123"
else
    echo -e "${GREEN}✓ Database has $USER_COUNT user(s)${NC}"
fi
echo ""

# Start the server
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Backend Server...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}API Server:${NC} http://localhost:$API_PORT"
echo -e "${GREEN}API Docs:${NC} http://localhost:$API_PORT/docs"
echo -e "${GREEN}Health Check:${NC} http://localhost:$API_PORT/health"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
python3 backend/main.py

