# 🌍 CrisisNexus — Federated Multi-NGO Crisis Coordination Platform

> A real-time crisis management system that connects Admins, NGOs, and Volunteers to coordinate disaster relief operations, resource allocation, and task assignments.

---

## 📋 Table of Contents

- [What This Project Does](#-what-this-project-does)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Setup (Step-by-Step)](#-quick-setup-step-by-step)
  - [Step 1 — Clone the Repository](#step-1--clone-the-repository)
  - [Step 2 — Set Up PostgreSQL Database](#step-2--set-up-postgresql-database)
  - [Step 3 — Configure Environment Variables](#step-3--configure-environment-variables)
  - [Step 4 — Set Up the Backend](#step-4--set-up-the-backend)
  - [Step 5 — Run Database Migrations](#step-5--run-database-migrations)
  - [Step 6 — Create Your First Admin](#step-6--create-your-first-admin)
  - [Step 7 — Set Up the Frontend](#step-7--set-up-the-frontend)
  - [Step 8 — Run the App](#step-8--run-the-app)
- [User Roles & What They Can Do](#-user-roles--what-they-can-do)
- [Platform Walkthrough](#-platform-walkthrough)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Environment Variables Reference](#-environment-variables-reference)

---

## 🎯 What This Project Does

CrisisNexus is a **federated disaster response coordination platform** with three distinct roles:

| Role | Capabilities |
|---|---|
| **Admin** | Approve NGOs & volunteers, assign tasks to multiple NGOs, manage resource inventory, view audit trails |
| **NGO Coordinator** | Accept assigned tasks, build volunteer teams, contribute resources, submit needs |
| **Volunteer** | View assigned tasks, accept/start/complete tasks, track personal progress |

Key features:
- ✅ Multi-NGO task assignment (one crisis → multiple NGOs work in parallel)
- ✅ Immutable task audit trail (every action timestamped)
- ✅ Resource contribution & inventory management
- ✅ Gamification (volunteer leaderboard, badges, streaks)
- ✅ Role-based dashboards with analytics

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, React Router, Axios, Lucide Icons |
| **Backend** | FastAPI (Python), Uvicorn |
| **Database** | PostgreSQL (via SQLAlchemy ORM + pg8000 driver) |
| **Auth** | JWT tokens (python-jose + passlib/bcrypt) |
| **NLP** | spaCy (en_core_web_sm model) |
| **Email** | fastapi-mail (SMTP/Gmail) |
| **Notifications** | Twilio (WhatsApp) |

---

## 🔧 Prerequisites

Make sure the following are installed **before** you begin:

### Required
- **Python 3.10 or higher** — [Download here](https://www.python.org/downloads/)
  ```bash
  python --version   # Should print Python 3.10+
  ```

- **Node.js 18 or higher** + npm — [Download here](https://nodejs.org/)
  ```bash
  node --version     # Should print v18+
  npm --version      # Should print 9+
  ```

- **PostgreSQL 14 or higher** — [Download here](https://www.postgresql.org/download/)
  ```bash
  psql --version     # Should print psql (PostgreSQL) 14+
  ```

- **Git** — [Download here](https://git-scm.com/)
  ```bash
  git --version
  ```

### Optional (for full features)
- Gmail account with [App Password](https://support.google.com/accounts/answer/185833) enabled — for email notifications
- Twilio account — for WhatsApp notifications
- Groq API key — for AI-powered NLP features
- OpenCage API key — for geocoding

> ⚠️ **The app works without email, Twilio, Groq, and OpenCage** — those features will simply be skipped.

---

## 🚀 Quick Setup (Step-by-Step)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/greenguru10/CrisisNexus.git
cd CrisisNexus
```

---

### Step 2 — Set Up PostgreSQL Database

Open your terminal and connect to PostgreSQL:

**On Windows (psql shell):**
```bash
psql -U postgres
```

**On Mac/Linux:**
```bash
sudo -u postgres psql
```

Then run these SQL commands inside the psql prompt:

```sql
-- Create the database
CREATE DATABASE CommunitySync1;

-- Verify it was created
\l

-- Exit psql
\q
```

> ℹ️ Remember your PostgreSQL **username** (usually `postgres`) and **password** — you'll need them in Step 3.

---

### Step 3 — Configure Environment Variables

#### Backend `.env`

Navigate to the backend folder and create a `.env` file:

```bash
cd backend
```

Create the file (copy-paste the block below and fill in your values):

**On Windows:**
```bash
copy NUL .env
```
**On Mac/Linux:**
```bash
touch .env
```

Now open `.env` in any text editor and paste:

```env
# ─── Database ────────────────────────────────────────────────────────────────
# Replace YOUR_PASSWORD with your PostgreSQL password
DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/CommunitySync1

# ─── Application ─────────────────────────────────────────────────────────────
APP_TITLE=CrisisNexus API
APP_VERSION=2.0.0
DEBUG=True

# ─── JWT Authentication ───────────────────────────────────────────────────────
# Change this to any long random string (keep it secret!)
JWT_SECRET=my-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=120

# ─── CORS (Frontend URL) ─────────────────────────────────────────────────────
CORS_ORIGINS=["http://localhost:3000"]

# ─── Email (Optional — leave blank to skip email features) ───────────────────
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587

# ─── Twilio WhatsApp (Optional) ───────────────────────────────────────────────
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE=

# ─── AI/NLP APIs (Optional) ───────────────────────────────────────────────────
GROQ_API_KEY=
OPENCAGE_API_KEY=
```

> ⚠️ Never commit your `.env` file to git. It is already in `.gitignore`.

#### Frontend `.env`

Go to the frontend folder:

```bash
cd ../frontend
```

Create `.env`:

**On Windows:**
```bash
copy NUL .env
```
**On Mac/Linux:**
```bash
touch .env
```

Paste this content:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

---

### Step 4 — Set Up the Backend

Go back to the backend folder:

```bash
cd ../backend
```

#### 4a. Create a Python virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

> You should now see `(venv)` at the start of your terminal prompt.

#### 4b. Install dependencies

```bash
pip install -r requirements.txt
```

> This takes 1–3 minutes. All packages from FastAPI to SQLAlchemy will be installed.

#### 4c. Install the spaCy language model (for NLP)

```bash
python -m spacy download en_core_web_sm
```

> If this fails, the app still runs — NLP will fall back to rule-based mode.

---

### Step 5 — Initialize the Database

Still inside `backend/` (with venv activated):

Run the master reset script to set up the entire schema from scratch with zero issues:

```bash
python reset_db.py
```

Expected output:
```
🧨 DATABASE RESET AND INITIALIZATION
Dropping all existing tables to start fresh...
✅ All tables dropped successfully.

Creating all tables from current ORM models...
✅ All tables created successfully!
🎉 Database successfully recreated from scratch with ZERO issues!
```

> ⚠️ **Warning:** Running this script will completely wipe the existing database and recreate it fresh. Do not run it if you wish to preserve the data!

---

### Step 6 — Create Your First Admin

```bash
python add_admin.py
```

You will be prompted:
```
📧 Enter admin email: admin@crisis.com
📱 Enter mobile number (optional, press Enter to skip): 
🔐 Enter password: 
🔐 Confirm password: 
✅ Admin user created successfully!
```

> Save these credentials — you'll use them to log in as Admin.

---

### Step 7 — Set Up the Frontend

Open a **new terminal window** (keep the backend terminal open), then:

```bash
cd CrisisNexus/frontend
npm install
```

> This installs all React dependencies. Takes 1–2 minutes.

---

### Step 8 — Run the App

You need **two terminals running simultaneously**:

#### Terminal 1 — Backend

```bash
cd CrisisNexus/backend

# Activate venv (if not already active)
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Start the server
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### Terminal 2 — Frontend

```bash
cd CrisisNexus/frontend
npm start
```

You should see:
```
Compiled successfully!
Local: http://localhost:3000
```

Your browser will automatically open `http://localhost:3000` 🎉

---

## 👥 User Roles & What They Can Do

### Admin
- Log in with the credentials you created in Step 6
- Approve / reject NGO registrations
- Approve / reject volunteer registrations
- Assign crisis needs to one or more NGOs
- Manage the resource inventory
- View analytics and leaderboard

### NGO Coordinator
- Register via the Landing page (`/`) → **NGO** section
- Wait for Admin to approve your NGO
- Accept/reject task assignments from Admin
- Assign volunteers to tasks (individual or team)
- Contribute resources to the admin inventory
- Submit new crisis needs for Admin review

### Volunteer
- Register via the Landing page (`/`) → **Volunteer** section
- Wait for Admin or NGO to approve your account
- View tasks assigned to you at `/tasks`
- Accept → Start → Complete tasks with feedback

---

## 🗺 Platform Walkthrough

| URL | Who Sees It | Purpose |
|---|---|---|
| `http://localhost:3000/` | Everyone | Landing page — login & register |
| `/dashboard` | All roles | Role-specific overview stats |
| `/needs` | Admin, NGO | Crisis needs management |
| `/tasks` | Volunteer | My assigned tasks |
| `/volunteers` | Admin, NGO | Volunteer management |
| `/resources` | Admin, NGO | Resource inventory |
| `/ngo-management` | Admin | Approve/reject NGOs |
| `/analytics` | Admin, NGO | Performance analytics |
| `/leaderboard` | All roles | Volunteer gamification board |
| `/profile` | All roles | Personal profile & settings |

---

## 📖 API Documentation

Once the backend is running, visit:

- **Interactive Docs (Swagger UI):** http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc):** http://127.0.0.1:8000/redoc

All endpoints are documented with request/response schemas and can be tested directly from the browser.

---

## 📁 Project Structure

```
CrisisNexus/
├── backend/
│   ├── .env                      ← Your environment variables (create this)
│   ├── main.py                   ← FastAPI app entry point
│   ├── database.py               ← SQLAlchemy session & engine
│   ├── requirements.txt          ← Python dependencies
│   ├── init_database.py          ← Initial DB setup script
│   ├── migrate_phase2.py         ← Phase 2 schema migration
│   ├── add_admin.py              ← Create first admin user
│   │
│   ├── models/                   ← SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── volunteer.py
│   │   ├── need.py
│   │   ├── ngo.py
│   │   ├── resource.py
│   │   ├── task_trail.py         ← Audit log model
│   │   ├── need_ngo_assignment.py
│   │   └── need_volunteer_assignment.py
│   │
│   ├── routes/                   ← API route handlers
│   │   ├── auth_routes.py
│   │   ├── need_routes.py
│   │   ├── volunteer_routes.py
│   │   ├── ngo_routes.py
│   │   ├── resource_routes.py
│   │   ├── task_routes.py
│   │   ├── trail_routes.py       ← Audit trail endpoints
│   │   ├── analytics_routes.py
│   │   ├── pool_routes.py
│   │   └── gamification_routes.py
│   │
│   ├── services/                 ← Business logic
│   │   ├── auth_service.py
│   │   ├── trail_service.py      ← Audit log writer
│   │   ├── gamification_service.py
│   │   ├── email_service.py
│   │   └── matching_service.py
│   │
│   ├── schemas/                  ← Pydantic request/response models
│   └── dependencies/             ← Auth middleware (JWT guards)
│
└── frontend/
    ├── .env                      ← Your frontend env vars (create this)
    ├── package.json
    └── src/
        ├── App.js                ← Routing
        ├── services/api.js       ← Axios instance with JWT header
        ├── components/
        │   ├── Sidebar.js
        │   ├── TopBar.js
        │   ├── TaskTrailPanel.js ← Slide-in audit timeline
        │   └── ProtectedRoute.js
        └── pages/
            ├── Landing.js        ← Login + register for all roles
            ├── Dashboard.js
            ├── Needs.js          ← Crisis needs management
            ├── VolunteerTasks.js ← Volunteer task view
            ├── Volunteers.js
            ├── NgoManagement.js
            ├── ResourceInventory.js
            ├── Analytics.js
            └── Leaderboard.js
```

---

## 🐛 Troubleshooting

### ❌ `could not connect to database`
- Make sure PostgreSQL is running
- Check your `DATABASE_URL` in `backend/.env` — password must be correct
- The database `CommunitySync1` must exist (see Step 2)

### ❌ `bcrypt` / passlib error on login
```
ValueError: password cannot be longer than 72 bytes
```
Fix: ensure `bcrypt==4.0.1` is installed (already pinned in `requirements.txt`):
```bash
pip install "bcrypt==4.0.1"
```

### ❌ `ModuleNotFoundError` when starting backend
Make sure your virtual environment is **activated** before running:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### ❌ Port 8000 already in use
```bash
# Windows — find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Mac/Linux
lsof -ti :8000 | xargs kill -9
```

### ❌ Port 3000 already in use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F

# Mac/Linux
lsof -ti :3000 | xargs kill -9
```

### ❌ Frontend shows blank page / API errors
- Ensure the backend is running on port 8000
- Check `frontend/.env` has `REACT_APP_API_URL=http://127.0.0.1:8000`
- Open browser DevTools → Console for specific errors

### ❌ `relation does not exist` (DB table missing)
Run the database reset script to recreate all tables correctly:
```bash
cd backend
python reset_db.py
```

### ❌ Volunteer tasks not appearing after NGO assigns them
This is fixed in the `phase2/federated-multi-ngo` branch. Make sure you are on this branch:
```bash
git checkout phase2/federated-multi-ngo
```

---

## 🔑 Environment Variables Reference

### `backend/.env`

| Variable | Required | Example | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ Yes | `postgresql+pg8000://postgres:pass@localhost:5432/CommunitySync1` | PostgreSQL connection string |
| `JWT_SECRET` | ✅ Yes | `my-long-random-secret` | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | ✅ Yes | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_MINUTES` | ✅ Yes | `120` | Token validity in minutes |
| `CORS_ORIGINS` | ✅ Yes | `["http://localhost:3000"]` | Allowed frontend origins |
| `EMAIL_USERNAME` | ⬜ No | `you@gmail.com` | Gmail address for sending emails |
| `EMAIL_PASSWORD` | ⬜ No | `abcd efgh ijkl mnop` | Gmail App Password (16 chars) |
| `TWILIO_ACCOUNT_SID` | ⬜ No | `ACxxxxxxxx` | Twilio SID for WhatsApp |
| `TWILIO_AUTH_TOKEN` | ⬜ No | `your-token` | Twilio auth token |
| `TWILIO_PHONE` | ⬜ No | `whatsapp:+14155238886` | Twilio sandbox number |
| `GROQ_API_KEY` | ⬜ No | `gsk_...` | Groq key for AI classification |
| `OPENCAGE_API_KEY` | ⬜ No | `abc123` | OpenCage key for geocoding |

### `frontend/.env`

| Variable | Required | Example | Description |
|---|---|---|---|
| `REACT_APP_API_URL` | ✅ Yes | `http://127.0.0.1:8000` | Backend base URL |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">
  Built with ❤️ for disaster response coordination
</div>
