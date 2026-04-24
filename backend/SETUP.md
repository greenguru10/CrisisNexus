# 🚀 Database Setup Guide

This document outlines the complete database setup process for the CrisisNexus backend.

## Prerequisites

- PostgreSQL database created and running (as mentioned in the terminal log: `community_sync3` database)
- Python 3.10+ with virtual environment activated
- All dependencies installed (`pip install -r requirements.txt`)
- `.env` file properly configured with database credentials

## Setup Steps

### Step 1: Initialize Database Tables

Create all required tables (users, volunteers, needs) from the ORM models:

```bash
cd backend
python init_database.py
```

**What this does:**
- Creates the `users` table with RBAC columns
- Creates the `volunteers` table for volunteer profiles
- Creates the `needs` table for crisis needs tracking
- Adds the `account_status` column to users table if not present
- Extends the `needstatus` enum with `accepted` and `in_progress` values

**Expected output:**
```
✅ ALL DATABASE SETUP STEPS COMPLETED SUCCESSFULLY!
🎉 Your database is ready to use!
```

### Step 2: Create Admin User (Optional but Recommended)

Create your first admin user to access the admin dashboard:

```bash
python add_admin.py
```

**Interactive prompts:**
- Email: `admin@your-email.com`
- Mobile: `+91XXXXXXXXXX`
- Password: (minimum 8 characters)

**Example:**
```bash
$ python add_admin.py
📧 Enter admin email: admin@crisis.com
📱 Enter mobile number (optional): +919876543210
🔐 Enter password: ••••••••
🔐 Confirm password: ••••••••
✅ Admin user created successfully!
```

### Step 3: (Optional) Generate Dummy Data

Populate the database with sample users, volunteers, and needs for testing:

```bash
python test_scripts/generate_dummy_data.py
```

**What this creates:**
- 1 admin user: `admin@test.com` (password: `admin123`)
- 1 NGO user: `ngo@test.com` (password: `ngo123`)
- 5 volunteer users: `volunteer1@test.com` to `volunteer5@test.com`
- 10 volunteer profiles with skills and locations
- 10 crisis needs with various categories and urgency levels

## Database Schema

### Users Table (`users`)
Stores authenticated users with role-based access control.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `email` | String(255) | Unique email identifier |
| `password_hash` | String(255) | Bcrypt hashed password |
| `role` | Enum | admin \| volunteer \| ngo |
| `mobile_number` | String(20) | For WhatsApp notifications |
| `is_active` | Boolean | Account activation status |
| `account_status` | Enum | pending \| approved \| rejected |
| `reset_token` | String(255) | For password reset flow |
| `reset_token_expiry` | DateTime | Expiry of reset token |
| `created_at` | DateTime | Account creation timestamp |

### Volunteers Table (`volunteers`)
Profiles of volunteers available for task assignment.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `name` | String(150) | Volunteer name |
| `email` | String(255) | Contact email |
| `mobile_number` | String(20) | WhatsApp number |
| `skills` | Array(String) | List of skills (e.g., ["first_aid", "driving"]) |
| `location` | String(255) | Human-readable location |
| `latitude` | Float | Geographic latitude |
| `longitude` | Float | Geographic longitude |
| `availability` | Boolean | Current availability status |
| `rating` | Float | Performance rating (0-5) |
| `created_at` | DateTime | Profile creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### Needs Table (`needs`)
Tracks crisis needs and their assignment status.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `raw_text` | Text | Original survey report text |
| `category` | String(50) | food \| water \| medical \| shelter \| etc. |
| `urgency` | Enum | low \| medium \| high |
| `people_affected` | Integer | Number of people affected |
| `location` | String(255) | Location of the need |
| `latitude` | Float | Geocoded latitude |
| `longitude` | Float | Geocoded longitude |
| `priority_score` | Float | AI-computed priority (0-100) |
| `status` | Enum | pending \| assigned \| accepted \| in_progress \| completed |
| `assigned_volunteer_id` | Integer | FK to volunteer |
| `feedback_rating` | Float | Post-completion rating (0-5) |
| `feedback_comments` | Text | Volunteer feedback |
| `created_at` | DateTime | Need creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

## Troubleshooting

### Connection Error
```
Error: could not connect to database
```
**Solution:** Verify PostgreSQL is running and `.env` contains correct credentials:
```
DATABASE_URL=postgresql+pg8000://postgres:PASSWORD@localhost:5432/community_sync3
```

### Table Already Exists
```
Error: relation "users" already exists
```
**Solution:** This is expected if you're re-running the script. It's safe to ignore.

### Enum Value Already Exists
```
Error: duplicate key
```
**Solution:** This means the enum already has the value. This is safe to ignore.

### Permission Denied
```
Error: permission denied for schema public
```
**Solution:** Ensure the PostgreSQL user has schema permissions:
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
```

## Verification

After setup, verify the database:

```bash
# List all users
python -c "from database import SessionLocal; from models.user import User; from sqlalchemy import select; db = SessionLocal(); print([u.email for u in db.execute(select(User)).scalars()])"

# Check table structure
psql -h localhost -U postgres -d community_sync3 -c "\dt"
```

## Starting the Server

Once database setup is complete:

```bash
uvicorn main:app --reload
```

The API will be available at:
- **API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Environment Variables

Ensure these are set in `.env`:

```env
# Database
DATABASE_URL=postgresql+pg8000://postgres:PASSWORD@localhost:5432/community_sync3

# Application
APP_TITLE=Smart Resource Allocation API
APP_VERSION=1.0.0
DEBUG=True

# JWT
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

# Email (optional)
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587

# WhatsApp (optional)
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE=whatsapp:+1234567890

# NLP/LLM
GROQ_API_KEY=your-groq-key
OPENCAGE_API_KEY=your-geocoding-key

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Project README](./README.md)
