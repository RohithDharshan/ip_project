    # Agentic AI–Driven Workflow Automation System
    ### PSG AI Consortium — Institutional Governance Platform

    A full-stack multi-agent AI system that automates institutional workflows including event approvals, procurement, and vendor selection.

    ---

    ## Architecture

    ```
    Frontend (React 18)  ←→  Backend (FastAPI)  ←→  SQLite/PostgreSQL
                                ↓
                ┌───────────────────────────────┐
                │         Agent Pipeline         │
                │  ProposalAgent → Compliance   │
                │  → RoutingAgent → Approvals   │
                │  → ProcurementAgent → Vendor  │
                └───────────────────────────────┘
    ```

    **5 AI Agents:**
    | Agent | Role |
    |-------|------|
    | ProposalAgent | NLP parsing, intent extraction, risk assessment |
    | RoutingAgent | Hierarchy-aware approval routing |
    | ComplianceAgent | Policy validation, budget limit checks |
    | ProcurementAgent | ERP-ready purchase order generation |
    | VendorAgent | Multi-criteria vendor scoring & recommendation |

    ---

    ## Quick Start (Local Development)

    ### Prerequisites
    - Python 3.11+
    - Node.js 18+
    - Git

    ### Option 1 — Automated Setup

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

    ### Option 2 — Manual Setup

    **Backend:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate          # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env              # Edit as needed
    python seed_data.py               # Seed database with demo data
    uvicorn main:app --reload --port 8000
    ```

    **Frontend** (in a new terminal):
    ```bash
    cd frontend
    npm install
    npm start                         # Opens at http://localhost:3000
    ```

    ### Option 3 — Docker Compose

    ```bash
    docker-compose up --build
    ```

    Access:
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000
    - API Docs: http://localhost:8000/docs

    ---

    ## Demo Accounts

    | Role | Email | Password |
    |------|-------|----------|
    | Faculty | faculty@psgai.edu.in | Password@123 |
    | Coordinator | coordinator@psgai.edu.in | Password@123 |
    | HoD | hod@psgai.edu.in | Password@123 |
    | Principal | principal@psgai.edu.in | Password@123 |
    | Bursar | bursar@psgai.edu.in | Password@123 |
    | Admin | admin@psgai.edu.in | Password@123 |

    ---

    ## Workflow

    ```
    1. Proposal Submission      → Student submits event/procurement proposal
    2. AI Analysis              → ProposalAgent extracts intent, budget category, risk
    3. Compliance Check         → ComplianceAgent validates against policies
    4. Routing                  → RoutingAgent determines required approvers
    5. HoD Approval             → Department head reviews
    6. Principal Approval       → For budgets > ₹50,000
    7. Bursar Approval          → Financial authorization
    8. Procurement Generation   → ProcurementAgent creates purchase orders
    9. Vendor Recommendation    → VendorAgent scores and ranks vendors
    10. Audit Logging           → Immutable audit trail for all actions
    ```

    ---

    ## API Reference

    Full interactive docs available at `http://localhost:8000/docs` (Swagger UI).

    **Key Endpoints:**

    | Method | Endpoint | Description |
    |--------|----------|-------------|
    | POST | `/auth/login` | Obtain JWT token |
    | GET | `/auth/me` | Current user info |
    | GET | `/proposals` | List all proposals |
    | POST | `/proposals` | Submit new proposal |
    | POST | `/proposals/{id}/process` | Trigger AI pipeline |
    | GET | `/approvals/pending` | Pending approvals for current user |
    | POST | `/approvals/{step_id}/decide` | Approve/Reject/Clarify |
    | GET | `/vendors/recommend` | AI vendor recommendations |
    | GET | `/analytics/overview` | KPI dashboard data |
    | GET | `/audit` | Full audit log |

    ---

    ## Project Structure

    ```
    IP Project/
    ├── backend/
    │   ├── agents/          # 5 AI agents + orchestrator
    │   ├── models/          # SQLAlchemy database models
    │   ├── routers/         # FastAPI route handlers
    │   ├── services/        # Audit & email services
    │   ├── config.py        # App configuration (Pydantic Settings)
    │   ├── database.py      # Async SQLAlchemy engine
    │   ├── main.py          # FastAPI app entry point
    │   ├── seed_data.py     # Demo data seeder
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── api/         # Axios API client
    │   │   ├── pages/       # React page components
    │   │   ├── App.js       # Router + Auth context
    │   │   └── utils.js     # Shared utilities
    │   └── package.json
    ├── docker-compose.yml
    ├── setup.sh
    └── README.md
    ```

    ---

    ## Configuration

    Copy `backend/.env.example` to `backend/.env` and configure:

    ```env
    SECRET_KEY=your-secret-key-here        # Change in production
    DATABASE_URL=sqlite+aiosqlite:///./app.db
    OPENAI_API_KEY=                        # Optional: enables LLM-enhanced agents
    SMTP_HOST=smtp.gmail.com               # Optional: email notifications
    ```

    ---

    ## Tech Stack

    - **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Python-JOSE
    - **Database**: SQLite (dev) / PostgreSQL (prod)
    - **Frontend**: React 18, React Router v6, Recharts, Axios
    - **Infrastructure**: Docker, Nginx, Uvicorn
    - **AI**: Rule-based agents with optional OpenAI integration
