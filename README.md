<div align="center">

  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white" />

  <br/><br/>

  # 🌍 CommunitySync

  ### Smart Resource Allocation & Volunteer Coordination System

  *An AI-powered, full-stack disaster response platform that transforms unstructured crisis reports into prioritized, actionable assignments — matching the right volunteer to the right need, instantly.*

  <br/>

  **NLP-Driven** · **Real-Time Dashboard** · **Role-Based Access** · **Auto Notifications**

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
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

### 🧠 AI & NLP Engine
- **Natural Language Processing** — Ingests raw, unstructured NGO survey reports using **spaCy** NER and keyword scoring to extract disaster category, urgency level, affected population, and geolocation.
- **Priority Scoring Engine** — Computes a weighted 0–100 severity index combining urgency (40%), affected scale (40%), and category criticality (20%).
- **Smart Volunteer Matching** — Algorithmically assigns the optimal volunteer using a composite of **Jaccard Skill Similarity** (50%), **Haversine Proximity** (35%), and **Performance Rating** (15%).

### 🔐 Authentication & Access Control
- **JWT-Based Auth** — Secure token authentication with configurable expiry for all API interactions.
- **Role-Based Access Control (RBAC)** — Three distinct user tiers with strictly enforced permissions:
  - **Admin** — Full system control: create/delete volunteers, match needs (auto or manual), unassign/reassign, view all data.
  - **NGO** — Upload crisis reports, view dashboard analytics, trigger volunteer matching.
  - **Volunteer** — View personal dashboard, upload field reports, update profile (location, mobile, password).

### 📬 Notification System
- **Email Notifications (SMTP)** — Automated HTML emails via `FastAPI-Mail` for assignment alerts, welcome messages, and password reset magic links.
- **WhatsApp Alerts (Twilio)** — Real-time WhatsApp messages dispatched to volunteers upon task assignment with location and category details.

### 📊 Interactive Frontend
- **Live Dashboard** — Real-time KPI cards showing total needs, completion rates, category/urgency breakdowns, and volunteer availability.
- **Needs Management Table** — Searchable, filterable table with status badges, priority scores, and inline volunteer assignment display (`→ Volunteer Name`).
- **Admin Controls** — Auto Match, Manual Match (dropdown picker), Unassign, and Reassign buttons directly in the interface.
- **Volunteer Cards** — Visual grid with skill tags, availability status, contact info, and admin delete controls.
- **Smooth UX** — Shimmer loading states, animated modals, hover transitions, and responsive Tailwind layouts.

### 📄 File Processing
- **Multi-Format Upload** — Supports **PDF**, **DOCX**, and **TXT** file ingestion with automatic text extraction.
- **NLP Pipeline** — Uploaded files flow through the same AI extraction pipeline as raw text reports.

### 👤 User Self-Service
- **Profile Settings** — All users can update their email, mobile number, location, and password.
- **Forgot Password Flow** — Time-limited JWT reset tokens dispatched via email with a dedicated reset UI.
- **Data Synchronization** — Profile changes by volunteers automatically propagate to both the `users` and `volunteers` tables.

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, React Router DOM, Tailwind CSS, Axios, Lucide Icons |
| **Backend** | FastAPI, Python 3.10, Uvicorn, Pydantic v2 |
| **Database** | PostgreSQL, SQLAlchemy 2.0, pg8000 (Pure Python Driver) |
| **AI / NLP** | spaCy (`en_core_web_sm`), Rule-based keyword extraction |
| **Authentication** | JWT (`python-jose`), bcrypt (`passlib`) |
| **Email** | FastAPI-Mail (`aiosmtplib`) |
| **Messaging** | Twilio API (WhatsApp Sandbox / Production) |
| **File Parsing** | PyPDF2, python-docx |
| **Testing** | Pytest, httpx, Faker |

---

## 🏗 System Architecture

CommunitySync operates on a **5-stage automated pipeline** that eliminates manual coordination overhead:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   📄 REPORT   │────▶│  🧠 NLP       │────▶│  🎯 PRIORITY  │────▶│  🤝 MATCHING  │────▶│  📬 NOTIFY    │
│   Upload     │     │  Extraction  │     │  Scoring     │     │  Engine      │     │  Email +     │
│   (Text/PDF) │     │  (spaCy)     │     │  (0-100)     │     │  (Jaccard +  │     │  WhatsApp    │
│              │     │              │     │              │     │   Haversine) │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Data Flow:**
1. **Report Ingestion** — NGO uploads raw text or PDF/DOCX file describing a crisis situation.
2. **NLP Extraction** — spaCy + keyword rules extract `category`, `urgency`, `people_affected`, and `location`.
3. **Priority Scoring** — Weighted formula assigns a 0–100 severity score determining response urgency.
4. **Volunteer Matching** — Algorithm cross-references skill sets, GPS proximity, and ratings to find the optimal responder.
5. **Notification Dispatch** — Matched volunteer receives automated Email + WhatsApp alert with deployment details.

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

> 📌 *Place your screenshots in a `/screenshots` directory at the project root.*

---

## 📡 API Endpoints

### 🔑 Authentication

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/auth/register` | Register a new user account | Public |
| `POST` | `/auth/login` | Authenticate and receive JWT token | Public |
| `GET` | `/auth/me` | Get current user profile | Authenticated |
| `PUT` | `/auth/me` | Update profile (email, mobile, location, password) | Authenticated |
| `POST` | `/auth/forgot-password` | Request password reset email | Public |
| `POST` | `/auth/reset-password` | Reset password with token | Public |

### 📋 Needs Management

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/api/upload-report` | Submit raw text report for NLP processing | Authenticated |
| `POST` | `/api/upload-file` | Upload PDF/DOCX/TXT report file | Authenticated |
| `GET` | `/api/needs` | List all needs (filterable by status, category, urgency) | Authenticated |
| `GET` | `/api/needs/{id}` | Get a single need by ID | Authenticated |

### 🤝 Matching & Assignment

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `POST` | `/api/match/{need_id}` | Auto-match best volunteer (AI scoring) | Admin / NGO |
| `POST` | `/api/match/{need_id}/manual` | Manually assign a specific volunteer | Admin |
| `POST` | `/api/match/{need_id}/unassign` | Remove volunteer from a need | Admin |

### 👥 Volunteer Management

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/volunteers` | List all volunteers | Authenticated |
| `POST` | `/api/volunteer` | Admin-create volunteer (auto-generates password, sends email) | Admin |
| `DELETE` | `/api/volunteer/{id}` | Delete a volunteer | Admin |

### 📊 Analytics

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| `GET` | `/api/dashboard` | Aggregated analytics (counts, breakdowns, averages) | Authenticated |

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

# Download spaCy language model
python -m spacy download en_core_web_sm

# Configure environment (see section below)
# Create .env file in backend/

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
```

> ⚠️ **Important:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password. For Twilio WhatsApp, recipients must first opt-in via the [Twilio Sandbox](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn).

---

## 🗺 Usage Flow

A typical end-to-end user journey through CommunitySync:

```
👤 Admin/NGO Login
       │
       ▼
📄 Upload Crisis Report (text or PDF/DOCX)
       │
       ▼
🧠 NLP Engine extracts: category, urgency, location, people affected
       │
       ▼
🎯 Priority Score computed (0-100)
       │
       ▼
📊 Need appears on Dashboard with severity ranking
       │
       ▼
🤝 Admin clicks "Auto Match" or "Manual" to assign a volunteer
       │
       ▼
📬 Volunteer receives Email + WhatsApp notification instantly
       │
       ▼
👤 Volunteer views assignment on their dashboard
       │
       ▼
🔄 Admin can Unassign / Reassign at any time
```

### Role-Specific Capabilities

| Action | Admin | NGO | Volunteer |
|--------|:-----:|:---:|:---------:|
| View Dashboard | ✅ | ✅ | ✅ |
| Upload Reports | ✅ | ✅ | ✅ |
| View Needs | ✅ | ✅ | ✅ |
| Auto/Manual Match | ✅ | ✅ | ❌ |
| Unassign / Reassign | ✅ | ❌ | ❌ |
| Create Volunteers | ✅ | ❌ | ❌ |
| Delete Volunteers | ✅ | ❌ | ❌ |
| View Volunteers List | ✅ | ✅ | ❌ |
| Edit Own Profile | ✅ | ✅ | ✅ |

---

## 🔭 Future Scope

| Feature | Description |
|---------|-------------|
| 🤖 **Predictive Crisis AI** | Ingest weather APIs and geopolitical feeds to proactively generate needs before disasters fully materialize |
| 📍 **Real-Time Volunteer Tracking** | WebSocket-powered live GPS tracking of deployed volunteers on a Leaflet/Mapbox interactive map |
| 🏢 **Multi-NGO Federation** | Isolated tenant workspaces allowing multiple NGOs to share volunteer pools while maintaining data sovereignty |
| 📱 **Mobile Application** | React Native offline-first mobile app for volunteers operating in low-connectivity disaster zones |
| 📈 **Historical Analytics** | Trend charts, response time tracking, and volunteer performance dashboards with exportable reports |
| 🌐 **Multi-Language NLP** | Expand NLP extraction to support Hindi, Bengali, Spanish, and other regional languages |
| 🔄 **Batch Processing** | Upload multiple reports simultaneously with progress tracking and bulk assignment capabilities |

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
