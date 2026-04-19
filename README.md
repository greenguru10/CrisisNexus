# 🌍 Smart Resource Allocation – Data-Driven Volunteer Coordination System

A production-ready **FastAPI** backend that accepts NGO survey reports (raw text or PDF/DOCX files), processes them using **NLP (spaCy)**, converts them into structured needs with priority scores, and matches the best available volunteers using a composite scoring engine.

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#-setup--installation)
- [Running the Server](#-running-the-server)
- [API Endpoints](#-api-endpoints)
- [Sample API Requests & Responses](#-sample-api-requests--responses)
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
- **Dashboard Analytics** – Real-time stats: total needs, category/urgency breakdowns, completion rates
- **Background Tasks** – Async logging via FastAPI BackgroundTasks
- **CORS Enabled** – Ready for React/frontend integration
- **Swagger Docs** – Auto-generated interactive API docs at `/docs`
- **Comprehensive Tests** – 22 tests covering NLP, priority scoring, matching, and API endpoints

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
| Testing | pytest + httpx |
| Dummy Data | Faker |
| Server | Uvicorn |

---

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI app entry point, CORS, route registration
├── config.py                  # Environment-based configuration (pydantic-settings)
├── database.py                # SQLAlchemy engine, session, Base
├── generate_dummy_data.py     # Script to seed DB with fake data
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not committed to git)
│
├── models/
│   ├── need.py                # Need ORM model (needs table)
│   └── volunteer.py           # Volunteer ORM model (volunteers table)
│
├── schemas/
│   ├── need_schema.py         # Pydantic schemas for need request/response
│   └── volunteer_schema.py    # Pydantic schemas for volunteer + match result
│
├── routes/
│   ├── need_routes.py         # POST /upload-report, /upload-file, GET /needs
│   ├── volunteer_routes.py    # POST /add-volunteer, GET /volunteers
│   └── matching_routes.py     # POST /match/{id}, GET /dashboard
│
├── services/
│   ├── nlp_service.py         # spaCy + keyword NLP extraction
│   ├── priority_service.py    # Weighted priority scoring (0-100)
│   └── matching_service.py    # Volunteer matching (skill + distance + rating)
│
├── utils/
│   └── location_utils.py      # Haversine formula + city geocoder
│
└── tests/
    └── test_api.py            # 22 pytest tests (NLP, priority, matching, API)
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
git clone <your-repo-url>
cd CommunitySync/backend
```

### 2. Create and activate virtual environment

```powershell
# Windows (PowerShell)
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

> **Note:** If `psql` is not on your PATH, use the full path:
> ```powershell
> & "C:\Program Files\PostgreSQL\<version>\bin\psql.exe" -U postgres -c "CREATE DATABASE community_sync;"
> ```

### 6. Configure environment variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/community_sync
APP_TITLE=Smart Resource Allocation API
APP_VERSION=1.0.0
DEBUG=True
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

> ⚠️ **Replace `YOUR_PASSWORD`** with your actual PostgreSQL password. Special characters must be URL-encoded (e.g., `@` → `%40`).

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

> Database tables are **auto-created** on server startup.

---

## 📡 API Endpoints

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | `GET` | `/` | Health check |
| 2 | `GET` | `/health` | Detailed health check |
| 3 | `POST` | `/api/upload-report` | Upload raw text survey report |
| 4 | `POST` | `/api/upload-file` | Upload PDF/DOCX/TXT report file |
| 5 | `GET` | `/api/needs` | List all needs (filterable by status, category, urgency) |
| 6 | `GET` | `/api/needs/{need_id}` | Get a single need by ID |
| 7 | `POST` | `/api/add-volunteer` | Register a new volunteer |
| 8 | `GET` | `/api/volunteers` | List all volunteers (filterable) |
| 9 | `GET` | `/api/volunteers/{id}` | Get a single volunteer by ID |
| 10 | `POST` | `/api/match/{need_id}` | Match best volunteer to a need |
| 11 | `GET` | `/api/dashboard` | Analytics dashboard |

---

## 📝 Sample API Requests & Responses

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
  "raw_text": "Urgent: 200 families in Kathmandu need clean drinking water and medical supplies immediately.",
  "category": "water",
  "urgency": "high",
  "people_affected": 200,
  "location": "Kathmandu",
  "latitude": 27.7172,
  "longitude": 85.324,
  "priority_score": 66.0,
  "status": "pending",
  "assigned_volunteer_id": null,
  "created_at": "2026-04-19T10:30:00Z",
  "updated_at": "2026-04-19T10:30:00Z"
}
```

---

### POST `/api/upload-file` — Upload a report file

**Request:** `multipart/form-data` with a PDF, DOCX, or TXT file

**Response:** Same as `/upload-report`

---

### POST `/api/add-volunteer` — Register a volunteer

**Request:**
```json
{
  "name": "Priya Sharma",
  "skills": ["medical", "first_aid", "logistics"],
  "location": "Mumbai, India",
  "latitude": 19.076,
  "longitude": 72.8777,
  "availability": true,
  "rating": 4.5
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Priya Sharma",
  "skills": ["medical", "first_aid", "logistics"],
  "location": "Mumbai, India",
  "latitude": 19.076,
  "longitude": 72.8777,
  "availability": true,
  "rating": 4.5,
  "created_at": "2026-04-19T10:30:00Z",
  "updated_at": "2026-04-19T10:30:00Z"
}
```

---

### POST `/api/match/{need_id}` — Match a volunteer

**Response (200):**
```json
{
  "need_id": 1,
  "volunteer_id": 5,
  "volunteer_name": "Priya Sharma",
  "match_score": 0.7125,
  "distance_km": 23.45,
  "skill_match": 0.6667,
  "message": "Volunteer Priya Sharma assigned to need 1"
}
```

---

### GET `/api/dashboard` — Analytics

**Response (200):**
```json
{
  "total_needs": 75,
  "pending_needs": 40,
  "assigned_needs": 25,
  "completed_needs": 10,
  "high_priority_needs": 30,
  "total_volunteers": 35,
  "available_volunteers": 20,
  "category_breakdown": {
    "food": 15,
    "medical": 20,
    "water": 10,
    "shelter": 8
  },
  "urgency_breakdown": {
    "high": 30,
    "medium": 25,
    "low": 20
  },
  "average_priority_score": 62.5
}
```

---

## 🧪 Running Tests

```bash
pytest tests/test_api.py -v
```

Tests use an **in-memory SQLite** database — no PostgreSQL required.

**Test coverage (22 tests):**
- ✅ NLP extraction (category, urgency, people count, location)
- ✅ Priority scoring (ranges, ordering, edge cases)
- ✅ Volunteer matching (proximity, skill match, availability)
- ✅ API endpoints (upload, list, filter, dashboard)

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

### 1. NLP Service (`services/nlp_service.py`)
- Uses **spaCy** for Named Entity Recognition (GPE/LOC entities)
- **Keyword scoring** to detect category (food, medical, water, shelter, etc.)
- **Urgency detection** via keyword matching (urgent, critical, emergency → high)
- **Regex-based** people count extraction (e.g., "200 families" → 200)

### 2. Priority Engine (`services/priority_service.py`)
```
priority_score = (urgency_weight × 40) + (people_factor × 40) + (category_weight × 20)
```
- Urgency: high=1.0, medium=0.6, low=0.3
- People factor: saturates at 1000 people
- Category: medical=1.0, water=0.9, food=0.85, shelter=0.75...

### 3. Matching Engine (`services/matching_service.py`)
```
match_score = (skill_score × 0.50) + (distance_score × 0.35) + (rating_score × 0.15)
```
- **Skill similarity:** Jaccard index between volunteer skills and category-relevant skills
- **Distance:** Haversine formula, inverse penalty (closer = higher score)
- **Rating:** Normalized 0–5 → 0–1

---

## 🗄 Database Schema

### `needs` table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| raw_text | Text | Original survey report |
| category | String(50) | food, medical, water, shelter, etc. |
| urgency | Enum | low, medium, high |
| people_affected | Integer | Number of people impacted |
| location | String(255) | Human-readable location |
| latitude | Float | GPS latitude |
| longitude | Float | GPS longitude |
| priority_score | Float | Computed score 0–100 |
| status | Enum | pending, assigned, completed |
| assigned_volunteer_id | Integer | FK to matched volunteer |
| created_at | Timestamp | Auto-set |
| updated_at | Timestamp | Auto-updated |

### `volunteers` table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| name | String(150) | Full name |
| skills | String[] | PostgreSQL array of skill tags |
| location | String(255) | Human-readable location |
| latitude | Float | GPS latitude |
| longitude | Float | GPS longitude |
| availability | Boolean | Currently available? |
| rating | Float | Performance rating 0–5 |
| created_at | Timestamp | Auto-set |
| updated_at | Timestamp | Auto-updated |

---

## 🔐 Environment Variables

All sensitive configuration lives in `.env` (never committed to git):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `APP_TITLE` | ❌ | API title (default: Smart Resource Allocation API) |
| `APP_VERSION` | ❌ | API version (default: 1.0.0) |
| `DEBUG` | ❌ | Enable debug mode (default: False) |
| `CORS_ORIGINS` | ✅ | JSON array of allowed origins |

---

## 🗺 Next Steps / Roadmap

### Immediate
- [ ] Add `.gitignore` for `venv/`, `__pycache__/`, `.env`, `.pytest_cache/`
- [ ] Add Redis caching for matching results
- [ ] Add authentication (JWT tokens) for API security
- [ ] Add pagination metadata to list endpoints

### Frontend Integration
- [ ] Build React/Next.js frontend dashboard
- [ ] Real-time updates via WebSockets
- [ ] Map visualization for needs and volunteers (Leaflet/Mapbox)

### Advanced Features
- [ ] Email/SMS notifications when volunteers are matched
- [ ] Volunteer feedback and rating system after task completion
- [ ] Historical analytics and trend charts
- [ ] Multi-language NLP support (Hindi, Bengali, etc.)
- [ ] AI-powered matching using ML models instead of rule-based scoring
- [ ] Batch file upload (multiple reports at once)
- [ ] Role-based access control (admin, NGO coordinator, volunteer)

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
