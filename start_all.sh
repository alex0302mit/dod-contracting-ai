#!/bin/bash

# Master Startup Script - Starts both Backend and Frontend

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DoD Contracting System - Full Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if tmux or screen is available for split terminal
if command -v tmux &> /dev/null; then
    echo -e "${GREEN}Using tmux for split terminal...${NC}"
    echo ""
    
    # Create new tmux session with split panes
    tmux new-session -d -s dod_contracting "cd '$SCRIPT_DIR' && ./start_backend.sh"
    tmux split-window -h -t dod_contracting "cd '$SCRIPT_DIR' && sleep 5 && ./start_frontend.sh"
    tmux select-layout -t dod_contracting tiled
    
    echo -e "${GREEN}✓ Started in tmux session 'dod_contracting'${NC}"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "   Attach to session: tmux attach -t dod_contracting"
    echo "   Detach: Press Ctrl+B then D"
    echo "   Kill session: tmux kill-session -t dod_contracting"
    echo ""
    
    # Attach to the session
    tmux attach -t dod_contracting
    
elif command -v screen &> /dev/null; then
    echo -e "${GREEN}Using screen for split terminal...${NC}"
    echo ""
    
    screen -dmS dod_contracting bash -c "cd '$SCRIPT_DIR' && ./start_backend.sh"
    screen -S dod_contracting -X screen bash -c "cd '$SCRIPT_DIR' && sleep 5 && ./start_frontend.sh"
    
    echo -e "${GREEN}✓ Started in screen session 'dod_contracting'${NC}"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "   Attach to session: screen -r dod_contracting"
    echo "   Detach: Press Ctrl+A then D"
    echo "   Kill session: screen -X -S dod_contracting quit"
    echo ""
    
    screen -r dod_contracting
    
else
    echo -e "${YELLOW}⚠  tmux/screen not available. Starting in sequence...${NC}"
    echo ""
    echo -e "${YELLOW}Starting backend in background...${NC}"
    ./start_backend.sh > backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo "   Backend PID: $BACKEND_PID"
    echo "   Logs: tail -f backend.log"
    
    echo ""
    echo -e "${YELLOW}Waiting 10 seconds for backend to start...${NC}"
    sleep 10
    
    echo ""
    echo -e "${YELLOW}Starting frontend (Ctrl+C will stop both)...${NC}"
    ./start_frontend.sh
    
    # Cleanup on exit
    trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM EXIT
fi

