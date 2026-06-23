# WealthWise AI 💰

### MCA Final Year Project — Intelligent Personal Finance Manager

> **Student:** Maanya Rajan | **HT No:** 2129-2486-2167

---

## Overview

WealthWise AI is a full-stack Django web application for smart personal finance management, featuring:

- **AI Expense Categorization** — TF-IDF + Logistic Regression auto-categorizes transactions
- **Voice Transaction Logging** — Web Speech API + NLP parser for natural language input
- **Receipt OCR Scanning** — Tesseract OCR with OpenCV preprocessing extracts transaction data
- **Predictive Forecasting** — Facebook Prophet & moving-average forecasting for future expenses
- **Smart Budget Tracking** — Real-time budget utilization with alerts
- **Personalized Recommendations** — Rule-based AI insights (50/30/20 rule, budget alerts, savings goals)
- **Group Expense Management** — Split bills equally among group members
- **Bill Reminders** — Automated Celery tasks send notifications before due dates
- **Interactive Dashboard** — Chart.js visualizations for spending trends

---

## Tech Stack

| Layer      | Technology                                 |
| ---------- | ------------------------------------------ |
| Backend    | Python 3.9+, Django 4.2                    |
| Frontend   | Tailwind CSS (CDN), Chart.js, Font Awesome |
| Database   | SQLite (dev) / PostgreSQL (prod)           |
| ML/AI      | scikit-learn, Prophet, NumPy, Pandas       |
| NLP        | Stanza, custom regex parser                |
| OCR        | Tesseract + OpenCV                         |
| Task Queue | Celery + Redis                             |
| Voice      | Web Speech API                             |

---

## Project Structure

```
wealthwise/
├── accounts/          # User auth, profiles
├── analytics/         # Dashboard, AI analytics, forecasting
│   └── ml/
│       ├── categorizer.py   # TF-IDF + LR transaction categorizer
│       ├── forecaster.py    # Prophet expense forecasting
│       └── recommender.py   # Financial recommendations engine
├── budgets/           # Budget management
├── groups/            # Group expense splitting
├── notifications/     # Bill reminders, Celery tasks
├── receipts/          # OCR receipt scanning
├── transactions/      # Transaction CRUD, categories
├── voice/             # Voice transaction logging
├── templates/         # HTML templates (Tailwind CSS)
└── wealthwise/        # Django project config
```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- Tesseract OCR: `brew install tesseract` (macOS) or `sudo apt install tesseract-ocr` (Ubuntu)
- Redis (for Celery): `brew install redis` (macOS) or `sudo apt install redis-server` (Ubuntu)

### Installation

```bash
# Clone / open project folder
cd wealthwise

# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
python manage.py runserver
```

### Running Celery (for bill reminders)

```bash
# In a separate terminal
source venv/bin/activate
celery -A wealthwise worker -l info
celery -A wealthwise beat -l info
```

Open **http://127.0.0.1:8000** and register a new account.

---

## Features Walkthrough

### 1. Dashboard

Real-time overview of income, expenses, balance, category breakdown (doughnut chart), monthly trend (bar chart), AI recommendations, active budgets, and 7-day expense forecast.

### 2. Transaction Management

Add/edit/delete transactions with smart auto-categorization. Filter by date, category, and type.

### 3. Voice Logging

Click the microphone and speak naturally:

> _"I spent 500 rupees on food today"_
> _"Received salary of 50000"_

The NLP parser extracts amount, type, date, and suggests a category.

### 4. Receipt Scanning

Upload a receipt photo — Tesseract OCR extracts merchant name, total amount, date, and line items. Review and save as a transaction.

### 5. AI Analytics

30-day expense forecast using Facebook Prophet, 12-month income/expense trend, daily spending patterns, and comprehensive recommendations.

### 6. Budget Tracking

Create monthly/weekly budgets with per-category allocations. Real-time progress bars and alerts at 75% and 90% usage.

### 7. Group Expenses

Create groups, add members, and split expenses equally. Automatic balance calculation per member.

### 8. Bill Reminders

Set recurring bill reminders. Celery background task checks daily and sends in-app (and email) notifications.

---

## Database Models

| Model                                      | App           | Description                                   |
| ------------------------------------------ | ------------- | --------------------------------------------- |
| UserProfile                                | accounts      | Extended user: income, currency, savings goal |
| Transaction                                | transactions  | Core financial record                         |
| Category                                   | transactions  | Default + custom categories                   |
| Budget / BudgetCategory                    | budgets       | Spending limits                               |
| ExpenseGroup / GroupExpense / ExpenseSplit | groups        | Shared expenses                               |
| Receipt                                    | receipts      | OCR-processed receipt images                  |
| BillReminder / Notification                | notifications | Alerts system                                 |

---

## License

This project is submitted as an academic final year project for MCA. All rights reserved.
