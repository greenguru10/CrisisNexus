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

### 📦 Automated Inventory Merging
When an NGO contributes resources, the system automatically checks for existing entries. If you contribute "Rice" and "Rice" already exists, the quantities are merged, maintaining a clean and efficient warehouse view.

### 🏆 Gamification & Incentives
- **Performance Points**: Earned by volunteers for every task.
- **The Pool Bonus**: Volunteers who assist "borrowing" NGOs receive **extra points**, incentivizing cross-organization help.
- **Streaks**: Consecutive task completions increase rank on the global leaderboard.

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
*   **My Tasks**: A simplified, mobile-friendly view of current assignments.
*   **Progress Tracker**: Move tasks through "Accept" → "Start" → "Complete" with real-time feedback.
*   **Achievement Board**: View personal stats, points, and leaderboard position to track impact.

---

## 🚀 Comprehensive Setup Guide

### Step 1: Prerequisites
Ensure you have the following installed:
- **PostgreSQL 14+** (Database)
- **Python 3.10+** (Backend Logic)
- **Node.js 18+** (Frontend UI)

### Step 2: Database Initialization (CRITICAL)
1.  **Create the Database**: Open your PostgreSQL terminal (psql) or PGAdmin and run:
    ```sql
    CREATE DATABASE community_sync3;
    ```
2.  **Configure Env**: In `/backend`, create a `.env` file:
    ```env
    DATABASE_URL=postgresql+pg8000://postgres:YOUR_PASSWORD@localhost:5432/community_sync3
    JWT_SECRET=any_random_secure_string
    ```
3.  **Run Schema Setup**: This script builds all tables, enums, and relations automatically.
    ```bash
    cd backend
    python scripts/setup_db.py
    ```

### Step 3: Backend Configuration
1.  **Virtual Environment**: Keep your system clean.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm  # Required for AI text analysis
    ```
3.  **Create Admin**: You must create a user to log in.
    ```bash
    python add_admin.py
    ```

### Step 4: Frontend Configuration
1.  **Install Node Modules**:
    ```bash
    cd ../frontend
    npm install
    ```
2.  **Set API URL**: Create a `.env` file in `/frontend`:
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
uvicorn main:app --reload --port 8000
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
- **`backend/scripts/`**: Maintenance and setup utilities.
- **`frontend/src/pages/`**: The distinct views for Admin, NGO, and Volunteers.
- **`frontend/src/components/`**: Reusable UI elements like the **TaskTrailPanel**.

---

## 🐛 Troubleshooting & Support

- **"Relation X does not exist"**: You missed Step 2. Run `python scripts/setup_db.py`.
- **"Connection Refused"**: Ensure your Backend is running on port 8000.
- **"Invalid Token"**: Clear your browser cookies or log in again; your JWT session might have expired.

---
**Built with ❤️ for Crisis Nexus — Empowering communities through federated coordination.**
