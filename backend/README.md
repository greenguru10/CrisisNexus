# 🌍 Smart Resource Allocation – Data-Driven Volunteer Coordination System

A production-ready **FastAPI** backend that accepts NGO survey reports (raw text or PDF/DOCX files), processes them using **NLP (spaCy)**, converts them into structured needs with priority scores, and matches the best available volunteers using a composite scoring engine.

**Now with:** JWT Authentication, Role-Based Access Control (RBAC), Email Notifications, and WhatsApp Messaging.

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#-setup--installation)
- [Database Migration](#-database-migration)
- [Running the Server](#-running-the-server)
- [Authentication & RBAC](#-authentication--rbac)
- [API Endpoints](#-api-endpoints)
- [Sample API Requests & Responses](#-sample-api-requests--responses)
- [Email & WhatsApp Notifications](#-email--whatsapp-notifications)
- [Running Tests](#-running-tests)
- [Dummy Data Generation](#-dummy-data-generation)
- [Core Modules](#-core-modules)
- [Database Schema](#-database-schema)
- [Environment Variables](#-environment-variables)
- [Next Steps / Roadmap](#-next-steps--roadmap)

---

## ✨ Features

- **NLP-Powered Report Processing** – Extracts category, urgency, people count, and location from unstructured survey text using spaCy + rule-based keyword matching
- **File Upload Support** – Upload reports as PDF, DOCX, or TXT files (text is auto-extracted)
- **Priority Scoring Engine** – Computes 0–100 priority scores based on urgency, people affected, and category weights
- **Volunteer Matching Engine** – Matches the best volunteer using skill similarity (Jaccard), Haversine distance, and rating
- **JWT Authentication** – Secure login with access tokens (OAuth2 password flow)
- **Role-Based Access Control** – Admin, Volunteer, and NGO roles with enforced permissions
- **Admin Volunteer Management** – Admins can update and delete volunteer records
- **Email Notifications** – Sends assignment and welcome emails via SMTP (Gmail)
- **WhatsApp Notifications** – Sends assignment messages via Twilio WhatsApp API
- **Dashboard Analytics** – Real-time stats: total needs, category/urgency breakdowns, completion rates
- **Background Tasks** – Async notifications via FastAPI BackgroundTasks
- **CORS Enabled** – Ready for React/frontend integration
- **Swagger Docs** – Auto-generated interactive API docs at `/docs`
- **Comprehensive Tests** – 33 tests covering NLP, priority scoring, matching, auth, and RBAC

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| Language | Python 3.10 |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| DB Driver | pg8000 (pure Python) |
| Validation | Pydantic v2 |
| NLP | spaCy (en_core_web_sm) |
| File Parsing | PyPDF2, python-docx |
| Authentication | JWT (python-jose + passlib/bcrypt) |
| Email | FastAPI-Mail (SMTP) |
| WhatsApp | Twilio API |
| Testing | pytest + httpx |
| Dummy Data | Faker |
| Server | Uvicorn |

---

## 📁 Project Structure

```
backend/
├── main.py                       # FastAPI app entry point, CORS, route registration
├── config.py                     # Environment-based configuration (pydantic-settings)
├── database.py                   # SQLAlchemy engine, session, Base
├── migrate.py                    # Database migration script (add columns)
├── generate_dummy_data.py        # Script to seed DB with fake data
├── add_volunteer.py              # Script to add a volunteer directly
├── send_notifications.py         # Script to test email + WhatsApp
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not committed to git)
│
├── models/
│   ├── need.py                   # Need ORM model (needs table)
│   ├── volunteer.py              # Volunteer ORM model (volunteers table)
│   └── user.py                   # User ORM model (users table) – auth + roles
│
├── schemas/
│   ├── need_schema.py            # Pydantic schemas for need request/response
│   ├── volunteer_schema.py       # Pydantic schemas for volunteer + match result
│   └── auth_schema.py            # Pydantic schemas for register/login/token
│
├── routes/
│   ├── auth_routes.py            # POST /auth/register, /auth/login, GET /auth/me
│   ├── need_routes.py            # POST /upload-report, /upload-file, GET /needs
│   ├── volunteer_routes.py       # CRUD volunteers + admin-only PUT/DELETE
│   └── matching_routes.py        # POST /match/{id}, GET /dashboard
│
├── services/
│   ├── auth_service.py           # JWT token creation/decode, bcrypt hashing
│   ├── nlp_service.py            # spaCy + keyword NLP extraction
│   ├── priority_service.py       # Weighted priority scoring (0-100)
│   ├── matching_service.py       # Volunteer matching (skill + distance + rating)
│   ├── email_service.py          # Email via FastAPI-Mail (SMTP)
│   └── whatsapp_service.py       # WhatsApp via Twilio API
│
├── dependencies/
│   └── auth_dependency.py        # get_current_user(), get_current_admin()
│
├── utils/
│   └── location_utils.py         # Haversine formula + city geocoder
│
└── tests/
    └── test_api.py               # 33 pytest tests (NLP, priority, matching, auth, RBAC)
```

---

## 📋 Prerequisites

1. **Python 3.10** – [Download](https://www.python.org/downloads/)
2. **PostgreSQL** – [Download](https://www.postgresql.org/download/windows/)
3. **Git** (optional) – For version control

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/VivekMaurya83/CommunitySync.git
cd CommunitySync/backend
```

### 2. Create and activate virtual environment

```powershell
# Windows (PowerShell) – use Python 3.10 specifically
py -3.10 -m venv venv
.\venv\Scripts\Activate
```

```bash
# Linux / macOS
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy language model

```bash
python -m spacy download en_core_web_sm
```

### 5. Create PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE community_sync;"
```

> **Note (Windows):** If `psql` is not on your PATH, use the full path:
> ```powershell
> & "C:\Program Files\PostgreSQL\<version>\bin\psql.exe" -U postgres -c "CREATE DATABASE community_sync;"
> ```

### 6. Configure environment variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/community_sync

# Application
APP_TITLE=Smart Resource Allocation API
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# JWT Authentication
JWT_SECRET=your_super_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

# Email (Gmail SMTP)
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE=whatsapp:+14155238886
```

> ⚠️ **Replace placeholders** with real values. Special characters in passwords must be URL-encoded (e.g., `@` → `%40`).

> 💡 **Generate a secure JWT secret:** `python -c "import secrets; print(secrets.token_hex(32))"`

> 💡 **Gmail App Password:** Go to [Google App Passwords](https://myaccount.google.com/apppasswords) and generate one for "Mail".

> 💡 **Twilio Sandbox:** Go to [Twilio Console → WhatsApp](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn), join the sandbox from your phone first.

---

## 🔄 Database Migration

If you're upgrading from a previous version (before auth/notifications were added):

```bash
python migrate.py
```

This adds the `email` and `mobile_number` columns to the `volunteers` table and creates the `users` table.

---

## ▶️ Running the Server

```bash
uvicorn main:app --reload
```

The server starts at: **http://127.0.0.1:8000**

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000 | Health check |
| http://127.0.0.1:8000/docs | Swagger UI (interactive API docs) |
| http://127.0.0.1:8000/redoc | ReDoc (alternative API docs) |

> Database tables (`needs`, `volunteers`, `users`) are **auto-created** on server startup.

---

## 🔐 Authentication & RBAC

### Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access: CRUD volunteers, match, upload, dashboard |
| **volunteer** | View own profile, view needs |
| **ngo** | View needs + volunteers, upload reports |

### Flow

1. **Register:** `POST /auth/register` → creates user with role
2. **Login:** `POST /auth/login` → returns JWT token
3. **Use token:** Add `Authorization: Bearer <token>` header to protected requests
4. **Swagger:** Click "Authorize" button (top right) in `/docs`, paste token

### Admin-Only Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `PUT` | `/api/volunteer/{id}` | Update volunteer details |
| `DELETE` | `/api/volunteer/{id}` | Delete a volunteer |

---

## 📡 API Endpoints

| # | Method | Endpoint | Auth | Description |
|---|--------|----------|------|-------------|
| 1 | `GET` | `/` | ❌ | Health check |
| 2 | `GET` | `/health` | ❌ | Detailed health check |
| 3 | `POST` | `/auth/register` | ❌ | Register new user |
| 4 | `POST` | `/auth/login` | ❌ | Login → JWT token |
| 5 | `GET` | `/auth/me` | 🔒 | Current user profile |
| 6 | `POST` | `/api/upload-report` | ❌ | Upload raw text report |
| 7 | `POST` | `/api/upload-file` | ❌ | Upload PDF/DOCX/TXT file |
| 8 | `GET` | `/api/needs` | ❌ | List all needs (filterable) |
| 9 | `GET` | `/api/needs/{id}` | ❌ | Get single need |
| 10 | `POST` | `/api/add-volunteer` | ❌ | Register a volunteer |
| 11 | `GET` | `/api/volunteers` | ❌ | List all volunteers |
| 12 | `GET` | `/api/volunteers/{id}` | ❌ | Get single volunteer |
| 13 | `PUT` | `/api/volunteer/{id}` | 🔒 Admin | Update volunteer |
| 14 | `DELETE` | `/api/volunteer/{id}` | 🔒 Admin | Delete volunteer |
| 15 | `POST` | `/api/match/{need_id}` | ❌ | Match best volunteer to need |
| 16 | `GET` | `/api/dashboard` | ❌ | Analytics overview |

---

## 📝 Sample API Requests & Responses

### POST `/auth/register` — Register a user

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "securepass123",
  "role": "admin"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-04-19T10:30:00Z"
}
```

---

### POST `/auth/login` — Get JWT token

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "securepass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "admin",
  "message": "Login successful"
}
```

---

### POST `/api/upload-report` — Submit a text report

**Request:**
```json
{
  "raw_text": "Urgent: 200 families in Kathmandu need clean drinking water and medical supplies immediately."
}
```

**Response (201):**
```json
{
  "id": 1,
  "raw_text": "Urgent: 200 families in Kathmandu need clean drinking water...",
  "category": "water",
  "urgency": "high",
  "people_affected": 200,
  "location": "Kathmandu",
  "latitude": 27.7172,
  "longitude": 85.324,
  "priority_score": 66.0,
  "status": "pending",
  "assigned_volunteer_id": null
}
```

---

### POST `/api/add-volunteer` — Register a volunteer

**Request:**
```json
{
  "name": "Vivek Maurya",
  "email": "vivekmaurya8311@gmail.com",
  "mobile_number": "+918766971682",
  "skills": ["logistics", "coordination", "first_aid"],
  "location": "India",
  "latitude": 26.85,
  "longitude": 80.91,
  "availability": true,
  "rating": 4.5
}
```

---

### PUT `/api/volunteer/{id}` — Admin update (requires JWT)

**Headers:** `Authorization: Bearer <admin_token>`

**Request:**
```json
{
  "email": "newemail@example.com",
  "availability": false,
  "skills": ["medical", "logistics"]
}
```

---

### POST `/api/match/{need_id}` — Match volunteer

**Response (200):** *(Also sends email + WhatsApp in background)*
```json
{
  "need_id": 1,
  "volunteer_id": 36,
  "volunteer_name": "Vivek Maurya",
  "match_score": 0.7125,
  "distance_km": 23.45,
  "skill_match": 0.6667,
  "message": "Volunteer Vivek Maurya assigned to need 1"
}
```

---

## 📧 Email & WhatsApp Notifications

Notifications are sent automatically when a volunteer is matched to a need via `POST /api/match/{need_id}`.

| Channel | Trigger | Configuration |
|---------|---------|---------------|
| **Email** | Volunteer assigned + User registered | Gmail SMTP (App Password) |
| **WhatsApp** | Volunteer assigned | Twilio Sandbox or Production |

Both services **gracefully degrade** — if credentials aren't configured, notifications are skipped without errors.

### Testing Notifications

```bash
python send_notifications.py
```

---

## 🧪 Running Tests

```bash
pytest tests/test_api.py -v
```

Tests use an **in-memory SQLite** database — no PostgreSQL required.

**Test coverage (33 tests):**
- ✅ NLP extraction (category, urgency, people count, location)
- ✅ Priority scoring (ranges, ordering, edge cases)
- ✅ Volunteer matching (proximity, skill match, availability)
- ✅ API endpoints (upload, list, filter, dashboard)
- ✅ Authentication (register, login, JWT validation)
- ✅ RBAC (admin-only update/delete, volunteer forbidden, unauthenticated blocked)

---

## 🗃 Dummy Data Generation

Seed the database with realistic fake data for testing:

```bash
python generate_dummy_data.py
```

This creates:
- **75 needs** — from realistic survey report templates across 15 cities
- **35 volunteers** — with randomized skills, locations, and ratings

---

## 🧠 Core Modules

### 1. Auth Service (`services/auth_service.py`)
- **bcrypt** password hashing via passlib
- **JWT** token creation with configurable expiry
- User authentication and email-based lookup

### 2. Auth Dependency (`dependencies/auth_dependency.py`)
- `get_current_user()` — decodes JWT, returns authenticated user
- `get_current_admin()` — ensures admin role
- `get_current_ngo_or_admin()` — ensures NGO or admin role

### 3. NLP Service (`services/nlp_service.py`)
- Uses **spaCy** for Named Entity Recognition (GPE/LOC entities)
- **Keyword scoring** to detect category (food, medical, water, shelter, etc.)
- **Urgency detection** via keyword matching (urgent, critical, emergency → high)
- **Regex-based** people count extraction (e.g., "200 families" → 200)

### 4. Priority Engine (`services/priority_service.py`)
```
priority_score = (urgency_weight × 40) + (people_factor × 40) + (category_weight × 20)
```

### 5. Matching Engine (`services/matching_service.py`)
```
match_score = (skill_score × 0.50) + (distance_score × 0.35) + (rating_score × 0.15)
```

### 6. Email Service (`services/email_service.py`)
- SMTP via FastAPI-Mail (Gmail compatible)
- Assignment notification with HTML template
- Welcome email on registration

### 7. WhatsApp Service (`services/whatsapp_service.py`)
- Twilio API integration
- Assignment notification with formatted message
- Graceful degradation if not configured

---

## 🗄 Database Schema

### `users` table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| email | String(255) | Unique, indexed |
| password_hash | String(255) | bcrypt hash |
| role | Enum | admin, volunteer, ngo |
| is_active | Boolean | Account active flag |
| created_at | Timestamp | Auto-set |

### `needs` table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| raw_text | Text | Original survey report |
| category | String(50) | food, medical, water, shelter, etc. |
| urgency | Enum | low, medium, high |
| people_affected | Integer | Number of people impacted |
| location | String(255) | Human-readable location |
| latitude / longitude | Float | GPS coordinates |
| priority_score | Float | Computed score 0–100 |
| status | Enum | pending, assigned, completed |
| assigned_volunteer_id | Integer | FK to matched volunteer |
| created_at / updated_at | Timestamp | Auto-managed |

### `volunteers` table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| name | String(150) | Full name |
| email | String(255) | Email for notifications |
| mobile_number | String(20) | WhatsApp number (e.g. +919876543210) |
| skills | String[] | PostgreSQL array of skill tags |
| location | String(255) | Human-readable location |
| latitude / longitude | Float | GPS coordinates |
| availability | Boolean | Currently available? |
| rating | Float | Performance rating 0–5 |
| created_at / updated_at | Timestamp | Auto-managed |

---

## 🔐 Environment Variables

All sensitive configuration lives in `.env` (never committed to git):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `CORS_ORIGINS` | ✅ | JSON array of allowed CORS origins |
| `JWT_SECRET` | ✅ | Secret key for JWT signing |
| `JWT_ALGORITHM` | ❌ | JWT algorithm (default: HS256) |
| `JWT_EXPIRY_MINUTES` | ❌ | Token expiry in minutes (default: 60) |
| `EMAIL_USERNAME` | ❌ | Gmail address for SMTP |
| `EMAIL_PASSWORD` | ❌ | Gmail App Password |
| `EMAIL_HOST` | ❌ | SMTP host (default: smtp.gmail.com) |
| `EMAIL_PORT` | ❌ | SMTP port (default: 587) |
| `TWILIO_ACCOUNT_SID` | ❌ | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | ❌ | Twilio Auth Token |
| `TWILIO_PHONE` | ❌ | Twilio WhatsApp number |
| `APP_TITLE` | ❌ | API title |
| `APP_VERSION` | ❌ | API version |
| `DEBUG` | ❌ | Debug mode (default: False) |

---

## 🗺 Next Steps / Roadmap

### Frontend Integration
- [ ] Build React/Next.js frontend dashboard
- [ ] Real-time updates via WebSockets
- [ ] Map visualization for needs and volunteers (Leaflet/Mapbox)
- [ ] Admin panel for volunteer management

### Advanced Features
- [ ] Redis caching for matching results
- [ ] Volunteer feedback and rating system after task completion
- [ ] Historical analytics and trend charts
- [ ] Multi-language NLP support (Hindi, Bengali, etc.)
- [ ] AI-powered matching using ML models
- [ ] Batch file upload (multiple reports at once)
- [ ] Password reset via email

### DevOps
- [ ] Dockerize the application
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Database migrations with Alembic

---

## 📄 License

MIT License

---

## 👥 Contributors

- Vivek Maurya
