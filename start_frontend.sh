#!/bin/bash

# DoD Contracting Frontend Startup Script

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DoD Contracting Frontend Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/dod_contracting_front_end"

# Step 1: Check Node.js version
echo -e "${YELLOW}[1/3] Checking Node.js version...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "   Please install Node.js from https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"
echo ""

# Step 2: Check npm version
echo -e "${YELLOW}[2/3] Checking npm version...${NC}"
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm $NPM_VERSION${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}[3/3] Checking dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies (this may take a few minutes)..."
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
echo ""

# Check if backend is running
echo -e "${YELLOW}Checking backend connection...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠  Backend is not running${NC}"
    echo "   Start it with: ./start_backend.sh"
    echo "   (Frontend will still start but API calls will fail)"
fi
echo ""

# Start the development server
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Frontend Development Server...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
echo ""
echo -e "${BLUE}📧 Test Login:${NC}"
echo "   Email: john.contracting@navy.mil"
echo "   Password: password123"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start Vite dev server
npm run dev

