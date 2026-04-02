# Zorvyn Finance Backend - Assignment Submission

## Overview
A secure financial dashboard backend built with FastAPI and SQLite. This project implements a robust Role-Based Access Control (RBAC) system and real-time data aggregation.

## Key Features
- **Persistence:** SQLite database managed via SQLAlchemy ORM.
- **Access Control:** Centralized dependency injection to enforce Admin, Analyst, and Viewer roles.
- **Summary Logic:** Dynamic calculation of net balance and category-specific totals.
- **Validation:** Pydantic schemas for strict data integrity.

## Setup & Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Run server: `python -m uvicorn main:app --reload`
3. Swagger Docs: `http://127.0.0.1:8000/docs`

## Assumptions & Notes
- The database comes pre-initialized with an Admin user (ID: 1) for evaluation purposes.
- The `verify_access` logic handles both user existence and role permissions.
