#!/bin/bash

# Stop all running servers

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping DoD Contracting System...${NC}"

# Kill tmux session if it exists
if tmux has-session -t dod_contracting 2>/dev/null; then
    tmux kill-session -t dod_contracting
    echo -e "${GREEN}✓ Stopped tmux session${NC}"
fi

# Kill screen session if it exists
if screen -list | grep -q dod_contracting 2>/dev/null; then
    screen -X -S dod_contracting quit
    echo -e "${GREEN}✓ Stopped screen session${NC}"
fi

# Kill any Python processes running main.py
pkill -f "python.*backend/main.py" && echo -e "${GREEN}✓ Stopped backend${NC}" || true

# Kill any npm processes
pkill -f "vite" && echo -e "${GREEN}✓ Stopped frontend${NC}" || true

echo -e "${GREEN}✓ All processes stopped${NC}"

