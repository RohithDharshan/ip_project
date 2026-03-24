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

    ## How to Run

    ### Step 1 — Install dependencies (first time only)

    **Backend:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate          # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python seed_data.py               # Populate the database with demo data
    ```

    **Frontend:**
    ```bash
    cd frontend
    npm install
    ```

    ### Step 2 — Start the backend

    ```bash
    cd backend
    source venv/bin/activate          # Windows: venv\Scripts\activate
    uvicorn main:app --reload --port 8000
    ```

    The API will be available at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

    ### Step 3 — Start the frontend (new terminal)

    ```bash
    cd frontend
    npm start
    ```

    Opens automatically at http://localhost:3000.

    ### Step 4 — Log in

    Use any of the demo accounts (see [Demo Accounts](#demo-accounts) below).

    ---

    ## Quick Start (Automated)

    ### Option 1 — Setup script

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

    ### Option 2 — Docker Compose

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
    | HoD | hod@psgai.edu.in | Password@123 |
    | Dean (Administration) | deanadmin@psgai.edu.in | Password@123 |
    | Dean (Autonomous) | deanautonomous@psgai.edu.in | Password@123 |
    | Principal | principal@psgai.edu.in | Password@123 |
    | Bursar | bursar@psgai.edu.in | Password@123 |
    | Admin | admin@psgai.edu.in | Password@123 |

    ---

    ## Workflow

    ```
    1. Proposal Submission      → Faculty submits event/procurement proposal
    2. AI Analysis              → Risk factors visible only to faculty
    3. Compliance Check         → ComplianceAgent validates against policies
    4. Routing                  → Fixed institutional chain is created
    5. HoD Approval             → Accept / Reject
    6. Bursar Approval          → Accept / Reject
    7. Dean (Administration)    → Accept / Reject
    8. Dean (Autonomous)        → Accept / Reject
    9. Principal Approval       → Accept / Reject
    10. Procurement Generation  → ProcurementAgent creates purchase orders
    11. Vendor Recommendation   → VendorAgent scores and ranks vendors
    12. Audit Logging           → Immutable audit trail for all actions
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
    | GET | `/proposals/{id}/analysis` | View AI risk & compliance analysis (faculty only) |
    | GET | `/approvals/pending` | Pending approvals for current user |
    | POST | `/approvals/{step_id}/decide` | Approve/Reject |
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
