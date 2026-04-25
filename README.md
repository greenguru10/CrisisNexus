# 🌍 CrisisNexus — Federated Multi-NGO Crisis Coordination Platform

> **Revolutionizing Disaster Relief through Real-Time Collaboration.**  
> CrisisNexus is a state-of-the-art crisis management system that bridges the gap between Admins, NGOs, and Volunteers. By leveraging a federated model, it enables multiple organizations to work together seamlessly on large-scale disasters.

---

## 📋 Table of Contents

1.  [🎯 Core Mission & Functionalities](#-core-mission--functionalities)
2.  [✨ Advanced Platform Features](#-advanced-platform-features)
3.  [👥 System Views & Functionalities](#-system-views--functionalities)
4.  [🚀 Comprehensive Setup Guide](#-comprehensive-setup-guide)
    - [Step 1: Prerequisites](#step-1-prerequisites)
    - [Step 2: Database Initialization](#step-2-database-initialization)
    - [Step 3: Backend Configuration](#step-3-backend-configuration)
    - [Step 4: Frontend Configuration](#step-4-frontend-configuration)
5.  [🛠 Running the Codebase](#-running-the-codebase)
6.  [📁 Project Architecture](#-project-architecture)
7.  [🐛 Troubleshooting & Support](#-troubleshooting--support)

---

## 🎯 Core Mission & Functionalities

CrisisNexus is designed to handle "Federated Relief Operations". In most systems, a task is assigned to one organization. In CrisisNexus, a single crisis "Need" (e.g., "Flooding in North Kerala") can be assigned to **multiple NGOs** simultaneously. 

### Key Capabilities:
- **Consensus-Driven Completion**: A task is only officially "Completed" once every participating NGO confirms their part is done.
- **Volunteer Lending (Pool)**: NGO A can "borrow" volunteers from NGO B if they are overwhelmed, ensuring no manpower goes to waste.
- **Smart Inventory**: A centralized resource pool fed by individual NGO contributions with automated item merging.

---

## ✨ Advanced Platform Features

### 🕒 Interactive Audit Trails (Slide-in Panel)
Every task tracks its own history. Using the **Audit Trail Panel**, you can see:
- Who created the task and when.
- Which NGOs accepted the assignment.
- Which resources (trucks, food, etc.) were allocated.
- Exactly which volunteer clicked the "Complete" button.

### 🗺️ Geospatial Intelligence & Heatmap
A fully integrated, interactive map powered by OpenStreetMap and React-Leaflet. It auto-clusters crisis markers to prevent UI clutter and features a dynamic density Heatmap layer that visually highlights high-priority disaster zones based on urgency and affected population.

### 📄 Hybrid OCR & Gemini Pre-Validation Engine
- **Image Preprocessing**: Automatically handles and parses uploaded images and scanned PDFs of handwritten reports via an EasyOCR-powered pipeline.
- **Smart Validation Gate**: A high-speed, fully asynchronous pre-pipeline LLM layer powered by **Google Gemini (gemini-2.5-flash)** in JSON mode ensures that only authentic, actionable disaster reports are processed, drastically reducing database spam.

### 🎨 Modern & Responsive UI
The entire frontend is built on a robust design system utilizing **pure Tailwind CSS utility classes**. Legacy inline styles have been entirely stripped out, ensuring a visually unified, performant, and easily maintainable codebase across all pages—from the Admin mapping view to the mobile-responsive Volunteer dashboard.

### 📦 Automated Inventory Merging
When an NGO contributes resources, the system automatically checks for existing entries. If you contribute "Rice" and "Rice" already exists, the quantities are merged, maintaining a clean and efficient warehouse view.

### 🏆 Gamification & Incentives
- **Performance Points**: Earned by volunteers for every task.
- **The Pool Bonus**: Volunteers who assist "borrowing" NGOs receive **extra points**, incentivizing cross-organization help.
- **Persistent Histories**: The Volunteer dashboard reliably stores and displays both active and completed task histories, showing cumulative impact.

---

## 👥 System Views & Functionalities

### 👑 Admin Domain (Command & Control)
*   **NGO Management**: Full lifecycle management of partner organizations (Approve/Reject/Suspend).
*   **Task Orchestration**: Breakdown crisis needs and assign them to the most capable NGOs.
*   **Resource Control**: Allocate trucks, medicine, and food from the global inventory to active crisis zones.
*   **Global Trail**: View the audit history of every task in the system to ensure transparency.

### 🏢 NGO Coordinator Domain (Resource Management)
*   **Active Needs**: View assignments from the Admin and accept or reject based on capacity.
*   **Volunteer Dispatch**: Build teams for specific tasks and manage their individual assignments.
*   **Pool Request Hub**: Submit requests for extra volunteers or approve lending your volunteers to other organizations.
*   **Resource Contribution**: Push local resources to the global Admin pool to support wider relief efforts.

### 👤 Volunteer Domain (Field Operations)
*   **My Tasks**: A simplified, mobile-friendly view of current assignments, featuring both active and previously completed tasks.
*   **Progress Tracker**: Move tasks through "Accept" → "Start" → "Complete" with real-time feedback.
*   **Achievement Board**: View personal stats, points, and leaderboard position to track impact.

---

## 🚀 Comprehensive Setup Guide

This guide covers everything you need to get the application running locally from scratch, including database initialization and environment configuration.

### Step 1: System Prerequisites
Ensure your development environment has the following installed:
- **PostgreSQL (14+)**: Required for relational data and robust querying.
- **Python (3.10+)**: Required for the FastAPI backend and AI pipelines.
- **Node.js (18+)**: Required for the React frontend.
- **C++ Build Tools / Visual Studio**: (Windows only) required for compiling `EasyOCR` dependencies.

---

### Step 2: Database Initialization (CRITICAL)

The application uses PostgreSQL. You must create the database before running any backend scripts.

1. **Open your PostgreSQL terminal (`psql`) or pgAdmin**.
2. **Create the database and user** by running the following SQL commands:
   ```sql
   -- Create a dedicated database for the application
   CREATE DATABASE community_sync3;
   
   -- (Optional but recommended) Create a dedicated user
   CREATE USER sync_admin WITH PASSWORD 'your_secure_password';
   
   -- Grant privileges to the user
   GRANT ALL PRIVILEGES ON DATABASE community_sync3 TO sync_admin;
   ```

---

### Step 3: Backend Configuration

The backend handles AI processing, API routing, and database interactions.

1. **Navigate to the backend directory and create a Virtual Environment**:
   ```bash
   cd backend
   python -m venv venv
   
   # Activate it (Windows):
   venv\Scripts\activate
   
   # Activate it (Mac/Linux):
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   
   # Download the required NLP model for SpaCy
   python -m spacy download en_core_web_sm
   ```
   *(Note: OpenCV, EasyOCR, and google-generativeai will automatically install from requirements.txt for the pipeline.)*

3. **Configure Environment Variables (`.env`)**:
   In the `backend` directory, create a file named `.env` and add the following:
   ```env
   # Database Connection String
   # Format: postgresql+pg8000://<user>:<password>@localhost:5432/<dbname>
   DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/community_sync3
   
   # Security
   JWT_SECRET=any_random_secure_string_here
   
   # Third-Party APIs
   GROQ_API_KEY=your_groq_api_key_here          # Required for LLM text extraction logic
   GEMINI_API_KEY=your_gemini_api_key_here      # Required for Gemini 2.5 Flash validation layer
   OPENCAGE_API_KEY=your_opencage_api_key_here  # Required for Map/Location Geocoding
   ```

4. **Run the Automated Setup Script**:
   This script builds all tables, enumerations, and relationships automatically.
   ```bash
   python scripts/setup_db.py
   ```

5. **Create an Admin Account**:
   You need an Admin account to access the main dashboard.
   ```bash
   python add_admin.py
   ```
   *(Follow the terminal prompts to set an email and password).*

---

### Step 4: Frontend Configuration

1. **Navigate to the frontend directory**:
   ```bash
   # From the root project folder
   cd frontend
   ```

2. **Install Node Modules**:
   ```bash
   npm install --legacy-peer-deps
   ```
   *(Note: `--legacy-peer-deps` is used to ensure React-Leaflet installs smoothly with React 18).*

3. **Set API URL**: 
   Create a `.env` file in the `/frontend` directory:
   ```env
   REACT_APP_API_URL=http://127.0.0.1:8000
   ```

---

## 🛠 Running the Codebase

Follow these steps in **two separate terminal windows**:

### Terminal 1: Backend Server
```bash
cd backend
# Ensure virtual environment is active (venv)
# Start the FastAPI server with auto-reload for development
uvicorn main:app --reload
```
*Comment: The backend handles all data logic, authentication, and the audit trail engine.*

### Terminal 2: Frontend UI
```bash
cd frontend
# Start the React development server
npm start
```
*Comment: The frontend provides the interactive dashboards and the live Audit Trail timeline.*

---

## 📁 Project Architecture

- **`backend/models/`**: Defines the data structure (Users, Tasks, Resources, Trails).
- **`backend/routes/`**: Handles API requests (e.g., `task_routes.py` manages the consensus completion).
- **`backend/services/`**: Houses the NLP, location extraction, and validation logic.
- **`backend/scripts/`**: Maintenance and setup utilities.
- **`frontend/src/pages/`**: The distinct views for Admin, NGO, and Volunteers.
- **`frontend/src/components/`**: Reusable UI elements like the **TaskTrailPanel**.

---

## 🐛 Troubleshooting & Support

- **"Relation X does not exist"**: You missed Step 2. Run `python scripts/setup_db.py`.
- **"Connection Refused"**: Ensure your Backend is running on port 8000.
- **"Invalid Token"**: Clear your browser cookies or log in again; your JWT session might have expired.
- **"Validation Layer Skipping"**: Ensure `GEMINI_API_KEY` is set correctly in the `.env` file. Without it, the system falls back to allowing all reports (fail-open).

---
**Built with ❤️ for Crisis Nexus — Empowering communities through federated coordination.**
