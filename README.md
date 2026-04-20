<div align="center">

  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq_LLM-FF6B35?style=for-the-badge&logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenCage-2ECC71?style=for-the-badge&logo=openstreetmap&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white" />

  <br/><br/>

  # 🌍 CommunitySync

  ### Smart Resource Allocation & Volunteer Coordination System

  *An AI-powered, full-stack disaster response platform that transforms unstructured crisis reports into prioritized, actionable assignments — matching the right volunteer to the right need, instantly. Powered by a hybrid NLP pipeline combining Groq LLM + rule-based extraction + OpenCage geocoding.*

  <br/>

  **Groq LLM + Rule-Based NLP** · **Volunteer Approval Workflow** · **OpenCage Geocoding** · **Task Lifecycle Tracking** · **Role-Based Access** · **Auto Notifications** · **Workload-Aware Matching**

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🔄 Task Lifecycle](#-task-lifecycle)
- [🛠 Tech Stack](#-tech-stack)
- [🏗 System Architecture](#-system-architecture)
- [📸 Screenshots](#-screenshots)
- [📡 API Endpoints](#-api-endpoints)
- [🚀 Setup & Installation](#-setup--installation)
- [🔐 Environment Variables](#-environment-variables)
- [🗺 Usage Flow](#-usage-flow)
- [🔭 Future Scope](#-future-scope)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### 🧠 Hybrid NLP Pipeline (Groq LLM + Rules)
- **10-Stage Pipeline** — `Raw Input → Preprocess → Summarize → Rule-based → Groq LLM → Location → Geocoding → Merge → Fallback → Output`
- **Groq LLM Integration (COMPULSORY)** — Uses `llama-3.1-8b-instant` via the Groq API for structured extraction of categories, people count, urgency, description, and location. Async with 15s timeout fallback.
- **Slang-Aware Preprocessing** — Normalizes 40+ mixed-language and shorthand terms: `khana → food`, `paani → water`, `ppl → people`, `bimaar → sick`, `madad → help`, `bachao → save`, `jaldi → quickly`, and more.
- **Multi-Category Detection** — Scores 8 categories (`food`, `water`, `medical`, `shelter`, `clothing`, `sanitation`, `education`, `logistics`) using word-boundary regex. Returns **all matched categories**, not just the top one.
- **Smart Summarization** — Long reports are automatically summarized by scoring sentences on disaster-keyword density and selecting the top 2–4 most relevant sentences.
- **Dual-Pattern People Extraction** — Detects counts via `"200 families"` OR `"people affected: 300"` patterns; falls back to any standalone number ≥ 10, then defaults to `5`.
- **Tiered Urgency Detection** — 25+ high-urgency phrases (`sos`, `life-threatening`, `mass casualty`, `bachao`, `turant`) before medium-level fallback.
- **Confidence Scoring** — LLM success → 90 (high), rule-based with matches → 65 (medium), fallback only → 40 (low).
- **Graceful Degradation** — If Groq is unavailable, falls back cleanly to rule-based extraction without errors.

### 📍 Location & Geocoding
- **3-Tier Location Extraction** — Groq LLM (primary) → spaCy NER GPE/LOC entities (secondary) → static city lookup (fallback).
- **OpenCage Geocoding API** — Real-time conversion of location names to `(latitude, longitude)` coordinates via the OpenCage API.
- **LRU Cache (256 entries)** — Geocoding results are cached in-memory to avoid repeated API calls for the same location.
- **Static City Fallback** — 20+ pre-loaded city coordinates (Mumbai, Delhi, Kathmandu, etc.) for instant offline geocoding.

### 🤖 Smart Volunteer Matching
- Composite score: **Jaccard Skill Similarity** (50%), **Haversine Proximity** (35%), **Performance Rating** (15%), plus **Workload Penalty**.
- Only **approved** volunteers are eligible for matching — pending/rejected accounts are excluded.

### 🔄 Task Lifecycle Tracking
- **5-Stage Pipeline**: `Pending → Assigned → Accepted → In Progress → Completed`
- **Volunteer Opt-In**: Volunteers must explicitly **Accept** an assignment before work begins — ensuring genuine commitment.
- **Interactive Status Actions**: Volunteers can progress tasks with dedicated stage buttons (Accept → Start → Complete).
- **Feedback & Ratings**: On task completion, volunteers submit a 1–5 star rating and comments stored for performance analytics.

### ✅ Volunteer Approval Workflow
- **Signup → Pending → Admin Review → Approved/Rejected** — New volunteer signups require admin approval before login.
- **Login Gating** — Unapproved volunteers receive `403 Forbidden` with a descriptive message (`"Account pending approval"` / `"Account has been rejected"`).
- **Admin Approval Dashboard** — Dedicated "Pending Approval" tab with Approve/Reject action buttons and pulsing badge count.
- **Auto Onboarding** — On approval, the system automatically sends a **Welcome Email** + **WhatsApp onboarding message** via background tasks.
- **Admin-Created Volunteers** — Auto-approved with a generated secure password emailed to the volunteer.
- **Assignment Gating** — Only approved volunteers can be matched/assigned to tasks.
- **Self-Service Skills** — Volunteers can add skills during registration and update them on their profile page.

### 🔐 Authentication & Role-Based Access Control (RBAC)
- **JWT-Based Auth** — Secure token authentication with configurable expiry.
- **Account Status Enforcement** — `account_status` field (`pending`/`approved`/`rejected`) on the User model gates volunteer access at the authentication layer.
- **Frontend RBAC Enforcement** — `<ProtectedRoute allowedRoles={[...]}>` wrapper on every React route; URL hacking redirects to a styled `/unauthorized` page.
- **Auth Utility Helpers** — Centralized `src/utils/auth.js` with `isAdmin()`, `isNGO()`, `isVolunteer()` functions used throughout the UI.
- **Three Distinct User Tiers:**

  | Role | Dashboard View | Key Capabilities |
  |------|---------------|-----------------|
  | **Admin** | Full analytics + 5-state lifecycle widgets + approval queue | Match/Unassign/Reassign needs, approve/reject volunteers |
  | **NGO** | Needs overview + urgency/category charts | Upload reports, view analytics |
  | **Volunteer** | Interactive "My Tasks" (Accept/Start/Complete) | Manage own assignments, submit feedback, edit skills |

### 📊 Role-Specific Dashboard Views
- **AdminDashboard** — 5-card lifecycle overview (Pending, Assigned, Accepted, In Progress, Completed), category/urgency breakdowns, volunteer capacity metrics.
- **NgoDashboard** — Crisis needs overview with progress bars per category and urgency distribution — no admin controls visible.
- **VolunteerDashboard** — Lands directly on the task management interface with action buttons and completion modal.

### 📬 Notification System
- **Email Notifications (SMTP)** — Automated HTML emails via `FastAPI-Mail` for assignment alerts, welcome messages, and password reset magic links.
- **WhatsApp Alerts (Twilio)** — Real-time WhatsApp messages dispatched to volunteers upon task assignment with location and category details.

### 📋 Needs Management (Visual Upgrade)
- **Rich Status Badges** — Icon + animated dot badges for each lifecycle state:
  - 🕐 `Pending` — grey with clock icon
  - ⚡ `Assigned` — blue with zap icon
  - ✅ `Accepted` — indigo with check icon
  - 🟣 `In Progress` — purple with **pinging dot + spinning loader**
  - ✔️ `Completed` — green with double-check icon
- **Action Column** — Context-aware buttons: `Auto Match`, `Manual`, `Unassign`, `Reassign`, `Volunteer Accepted`, `Active Now`, `Completed` — no more plain text.

### 👤 Profile Settings (Redesigned)
- **Avatar with Initials** — Gradient circle generated from email initials.
- **Role Badge** — Color-coded pill (Admin = red, NGO = purple, Volunteer = green).
- **Smart Field Sync** — Mobile number and location automatically pulled from volunteer table if missing from user account record.
- **Auto-dismiss Success Toast** — Green confirmation disappears after 4 seconds automatically.
- **Skeleton Loading** — Shimmer placeholder renders while profile data fetches.

### 📄 File Processing
- **Multi-Format Upload** — Supports **PDF**, **DOCX**, and **TXT** file ingestion with automatic text extraction through the same NLP pipeline.

---

## 🔄 Task Lifecycle

```
  ┌──────────┐    Admin assigns    ┌──────────┐   Volunteer accepts  ┌──────────┐
  │ PENDING  │ ─────────────────▶ │ ASSIGNED │ ─────────────────▶  │ ACCEPTED │
  └──────────┘                    └──────────┘                      └────┬─────┘
                                                                         │ Volunteer starts
                                                                         ▼
                                                                   ┌───────────┐
                                                                   │ IN PROGRESS│
                                                                   └─────┬──────┘
                                                                         │ Volunteer completes
                                                                         ▼
                                                                   ┌───────────┐
                                                                   │ COMPLETED  │
                                                                   └───────────┘
```

Each transition is validated server-side. Invalid transitions (e.g., jumping from `pending` to `in_progress`) return a `400 Bad Request`.

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, React Router DOM, Tailwind CSS, Axios, Lucide Icons |
| **Backend** | FastAPI, Python 3.10, Uvicorn, Pydantic v2 |
| **Database** | PostgreSQL, SQLAlchemy 2.0, pg8000 (Pure Python Driver) |
| **AI / NLP** | Groq LLM (`llama-3.1-8b-instant`), spaCy (`en_core_web_sm`), Rule-based keyword extraction |
| **Geocoding** | OpenCage Geocoding API (with LRU cache), Haversine distance calculation |
| **Authentication** | JWT (`python-jose`), bcrypt (`passlib`), Account status gating |
| **RBAC** | Frontend `<ProtectedRoute>` + Backend role dependency injection |
| **Email** | FastAPI-Mail (`aiosmtplib`) |
| **Messaging** | Twilio API (WhatsApp Sandbox / Production) |
| **File Parsing** | PyPDF2, python-docx |
| **Testing** | Pytest, httpx, Faker |

---

## 🏗 System Architecture

CommunitySync operates on a **10-stage hybrid AI pipeline:**

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 📄 REPORT │──▶│🔤 PREPROC │──▶│📝 SUMMAR- │──▶│📏 RULE   │──▶│🤖 GROQ   │
│  Upload  │   │ Slang    │   │  IZE     │   │ BASED    │   │  LLM     │
│(Text/PDF)│   │ 40+ maps │   │(long txt)│   │ Extract  │   │ Extract  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └────┬─────┘
                                                                  │
     ┌────────────────────────────────────────────────────────────┘
     ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│🔀 MERGE  │──▶│📍 GEOCODE│──▶│ 🎯 SCORE │──▶│ 🤝 MATCH │──▶│ 📬 NOTIFY│
│ LLM +    │   │ OpenCage │   │  0-100   │   │ Workload │   │ Email +  │
│ Rules    │   │ Cached   │   │ Priority │   │  Aware   │   │ WhatsApp │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────┐
                                                       │ 🔄 TASK LIFECYCLE │
                                                       │ Accept→Start→Done │
                                                       └──────────────────┘
```

**Data Flow:**
1. **Report Ingestion** — NGO uploads raw text or PDF/DOCX describing a crisis.
2. **Preprocessing** — Slang normalization, whitespace cleanup, mixed-language expansion.
3. **NLP Extraction** — spaCy + keyword rules extract `category`, `urgency`, `people_affected`, `location`.
4. **Priority Scoring** — Weighted formula assigns a 0–100 severity score.
5. **Workload-Aware Matching** — Algorithm cross-references skills, GPS proximity, ratings, and current active task count.
6. **Notification Dispatch** — Matched volunteer receives Email + WhatsApp alert.
7. **Task Lifecycle** — Volunteer accepts, starts, and completes the task with feedback submission.

---

## 📸 Screenshots

<div align="center">

| Dashboard | Needs Page |
|:---------:|:----------:|
| <img width="1911" height="969" alt="Screenshot 2026-04-19 171724" src="https://github.com/user-attachments/assets/094aad04-b2a6-42d7-a299-57919f475875" /> | <img width="1905" height="956" alt="Screenshot 2026-04-19 171752" src="https://github.com/user-attachments/assets/0f4ccc0f-8297-41ab-8524-84d6b1b9500b" /> |

| Volunteers Page | Upload Report |
|:---------------:|:-------------:|
| <img width="1918" height="957" alt="Screenshot 2026-04-19 171935" src="https://github.com/user-attachments/assets/33cf6a5a-36dc-48db-b478-29852ebe7ca6" /> | <img width="1643" height="913" alt="Screenshot 2026-04-19 171816" src="https://github.com/user-attachments/assets/fceaa7bd-8fae-4788-a56a-83dc34d98ade" /> |

| Login Page | Profile Settings |
|:----------:|:----------------:|
| <img width="1918" height="968" alt="Screenshot 2026-04-19 171956" src="https://github.com/user-attachments/assets/de2f64c5-e43c-44bd-821d-3d688fb95a4b" /> | <img width="1916" height="916" alt="Screenshot 2026-04-19 171838" src="https://github.com/user-attachments/assets/519d49f5-91a2-45b1-9694-aff11cf3cd57" /> |

</div>

---

## 📡 API Endpoints

### 🔑 Authentication

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/auth/register` | Register user (volunteers start as `pending`, auto-creates volunteer profile with skills) | Public |
| `POST` | `/auth/login` | Authenticate & get JWT (blocks unapproved volunteers with `403`) | Public |
| `GET` | `/auth/me` | Get profile (syncs mobile/location/skills from volunteer record) | Authenticated |
| `PUT` | `/auth/me` | Update profile (email, mobile, location, skills, password) | Authenticated |
| `POST` | `/auth/forgot-password` | Request password reset email | Public |
| `POST` | `/auth/reset-password` | Reset password with token | Public |

### 📋 Needs Management

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/api/upload-report` | Submit raw text → **hybrid NLP pipeline** (LLM + rules + geocoding) | Authenticated |
| `POST` | `/api/upload-file` | Upload PDF/DOCX/TXT → same hybrid pipeline | Authenticated |
| `GET` | `/api/needs` | List all needs (filterable by status, category, urgency) | Authenticated |
| `GET` | `/api/needs/{id}` | Get a single need by ID | Authenticated |

### 🤝 Matching & Assignment

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/api/match/{need_id}` | Auto-match best **approved** volunteer (workload-aware AI scoring) | Admin / NGO |
| `POST` | `/api/match/{need_id}/manual` | Manually assign a specific **approved** volunteer | Admin |
| `POST` | `/api/match/{need_id}/unassign` | Remove volunteer from a need | Admin |

### 🔄 Task Lifecycle (Volunteer Actions)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/task/my-tasks` | Get all needs assigned to the current volunteer | Volunteer |
| `POST` | `/api/task/{need_id}/accept` | Volunteer accepts assignment → status: `accepted` | Volunteer |
| `POST` | `/api/task/{need_id}/start` | Volunteer starts work → status: `in_progress` | Volunteer |
| `POST` | `/api/task/{need_id}/complete` | Volunteer completes task with rating/comments → status: `completed` | Volunteer |

### 👥 Volunteer Management & Approval

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/volunteers` | List all **approved** volunteers | Admin / NGO |
| `GET` | `/api/volunteers/pending` | List volunteers awaiting approval | Admin |
| `POST` | `/api/volunteer/{id}/approve` | Approve pending volunteer (triggers welcome email + WhatsApp) | Admin |
| `POST` | `/api/volunteer/{id}/reject` | Reject pending volunteer | Admin |
| `POST` | `/api/volunteer` | Admin-create volunteer (auto-approved, sends credentials email) | Admin |
| `PUT` | `/api/volunteer/{id}` | Update volunteer details | Admin |
| `DELETE` | `/api/volunteer/{id}` | Delete a volunteer and their user account | Admin |

### 📊 Analytics

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/dashboard` | Aggregated analytics — includes all 5 lifecycle state counts | Authenticated |

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **PostgreSQL** — [Download](https://www.postgresql.org/download/)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/CommunitySync.git
cd CommunitySync
```

### 2️⃣ Database Setup
```bash
psql -U postgres -c "CREATE DATABASE community_sync;"
```

### 3️⃣ Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\Activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Groq LLM client
pip install groq

# Download spaCy language model
python -m spacy download en_core_web_sm

# Configure environment (see section below)
# Create .env file in backend/

# Run database migrations (required once after first setup)
python fix_enum.py
python migrate_account_status.py

# Start the server
uvicorn main:app --reload
```
> Backend runs at **http://127.0.0.1:8000** — Swagger docs at **http://127.0.0.1:8000/docs**

### 4️⃣ Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```
> Frontend runs at **http://localhost:3000**

### 5️⃣ Seed Test Data (Optional)
```bash
cd backend
python test_scripts/generate_dummy_data.py
```

> ⚠️ **Note on Migrations:** If upgrading an existing database:
> - `python fix_enum.py` — Adds `ACCEPTED`/`IN_PROGRESS` values to the `needstatus` enum.
> - `python migrate_account_status.py` — Adds the `account_status` column to the `users` table (idempotent, safe to run multiple times).

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory with the following configuration:

```env
# ── Database ─────────────────────────────────────────────────────
DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/community_sync

# ── Application ──────────────────────────────────────────────────
APP_TITLE=Smart Resource Allocation API
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=["http://localhost:3000"]

# ── JWT Authentication ───────────────────────────────────────────
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=1440

# ── Email (SMTP via FastAPI-Mail) ────────────────────────────────
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_FROM=your.email@gmail.com

# ── Twilio WhatsApp ──────────────────────────────────────────────
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE=+14155238886
TWILIO_JOIN_CODE=store-creature

# ── Groq LLM (required for AI-powered NLP extraction) ───────────
GROQ_API_KEY=gsk_your_groq_api_key_here

# ── OpenCage Geocoding (required for location-to-coordinates) ────
OPENCAGE_API_KEY=your_opencage_api_key_here
```

> ⚠️ For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password. For Twilio WhatsApp, recipients must first opt-in via the [Twilio Sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn). Get a free Groq API key at [console.groq.com](https://console.groq.com). Get a free OpenCage API key at [opencagedata.com](https://opencagedata.com/users/sign_up).

---

## 🗺 Usage Flow

### Admin / NGO Flow
```
👤 Login (Admin / NGO)
       │
       ▼
📄 Upload Crisis Report (text or PDF/DOCX)
       │
       ▼
🔤 Slang Preprocessing (40+ terms: khana→food, paani→water, ppl→people…)
       │
       ▼
📝 Summarize long text (top 2-4 sentences by keyword density)
       │
       ▼
📏 Rule-Based Extraction (multi-category, urgency, people count, spaCy NER)
       │
       ▼
🤖 Groq LLM Extraction (structured JSON via llama-3.1-8b-instant)
       │
       ▼
🔀 Merge Results (LLM preferred, rule-based fallback) → Confidence Score
       │
       ▼
📍 OpenCage Geocoding (location → lat/lon, cached)
       │
       ▼
🎯 Priority Score computed (0–100)
       │
       ▼
📊 Need appears on Dashboard with status badge "Pending"
       │
       ▼
🤝 Admin clicks "Auto Match" (only approved volunteers, workload-aware)
       │
       ▼
📬 Volunteer receives Email + WhatsApp alert → Status: "Assigned"
```

### Volunteer Flow
```
👤 Volunteer logs in → Lands directly on "My Tasks"
       │
       ▼
✅ Clicks "Accept Assignment" → Status: "Accepted"
       │
       ▼
▶️  Clicks "Make In-Progress" → Status: "In Progress"
       │
       ▼
✔️  Clicks "Complete Task" → Rating modal appears
       │
       ▼
⭐ Submits 1–5 stars + comments → Status: "Completed"
```

### Role-Specific Capabilities

| Action | Admin | NGO | Volunteer |
|--------|:-----:|:---:|:---------:|
| View Dashboard (role-specific) | ✅ Full Analytics | ✅ Needs Overview | ✅ My Tasks |
| Upload Reports | ✅ | ✅ | ✅ |
| View Needs Table | ✅ | ✅ | ❌ |
| Auto / Manual Match (approved only) | ✅ | ✅ | ❌ |
| Unassign / Reassign | ✅ | ❌ | ❌ |
| Approve / Reject Volunteers | ✅ | ❌ | ❌ |
| Create Volunteers (auto-approved) | ✅ | ❌ | ❌ |
| Delete Volunteers | ✅ | ❌ | ❌ |
| View Volunteers List | ✅ | ❌ | ❌ |
| Accept / Start / Complete Tasks | ❌ | ❌ | ✅ |
| Submit Task Feedback & Rating | ❌ | ❌ | ✅ |
| Edit Own Profile + Skills | ✅ | ✅ | ✅ |
| Access `/volunteers` URL directly | ✅ | 🚫 Redirected | 🚫 Redirected |

---

## 🔭 Future Scope

| Feature | Description |
|---------|-------------|
| 🤖 **Predictive Crisis AI** | Ingest weather APIs and geopolitical feeds to proactively generate needs before disasters fully materialize |
| 📍 **Real-Time Volunteer Tracking** | WebSocket-powered live GPS tracking of deployed volunteers on a Leaflet/Mapbox interactive map |
| 🏢 **Multi-NGO Federation** | Isolated tenant workspaces allowing multiple NGOs to share volunteer pools while maintaining data sovereignty |
| 📱 **Mobile Application** | React Native offline-first mobile app for volunteers operating in low-connectivity disaster zones |
| 📈 **Performance Analytics** | Volunteer performance dashboards using `feedback_rating` data — trend charts and response time tracking |
| 🌐 **Extended NLP Language Support** | Expand slang/mixed-language map to cover Bengali, Tamil, Spanish, Swahili, and other regional languages |
| 🔄 **Batch Processing** | Upload multiple reports simultaneously with progress tracking and bulk assignment capabilities |
| 🔗 **WhatsApp Command Webhooks** | Allow volunteers to reply "accept 101" via WhatsApp to trigger lifecycle transitions through Twilio webhook |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push** to the branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

  **Built with ❤️ for communities that need it most.**

  <br/>

  ⭐ *Star this repo if you found it useful!* ⭐

</div>
