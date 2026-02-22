#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════
#  AgentFlow — One-Time Setup Script
#  Agentic AI–Driven Workflow Automation System
# ════════════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════════════╗"
echo "  ║   🤖 AgentFlow — Agentic AI Workflow Automation   ║"
echo "  ║      PSG AI Consortium | Institutional Governance ║"
echo "  ╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Python virtual environment ───────────────────────────────────
echo -e "${YELLOW}[1/4] Setting up Python virtual environment…${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}      ✓ Python environment ready${NC}"

# ── 2. Copy env file ─────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${GREEN}      ✓ Created .env from template${NC}"
fi
cd ..

# ── 3. Node / npm install ────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Installing frontend dependencies…${NC}"
cd frontend
npm install --silent
echo -e "${GREEN}      ✓ Node dependencies ready${NC}"
cd ..

echo -e "${YELLOW}[3/4] Setup complete!${NC}"
echo ""
echo -e "${CYAN}══════════════════════════════════════════"
echo "  To start the application:"
echo ""
echo "  Terminal 1 (backend):"
echo "    cd backend && source venv/bin/activate"
echo "    python main.py"
echo ""
echo "  Terminal 2 (frontend):"
echo "    cd frontend && npm start"
echo ""
echo "  Then open: http://localhost:3000"
echo ""
echo "  API docs:  http://localhost:8000/docs"
echo ""
echo "  Demo login:"
echo "    Email:    faculty@psgai.edu.in"
echo "    Password: Password@123"
echo -e "══════════════════════════════════════════${NC}"
