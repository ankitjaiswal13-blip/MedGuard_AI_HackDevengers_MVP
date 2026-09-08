# MedGuard AI

**AI-powered medicine inventory and demand forecasting system** for the Hack Devengers 2.0 MVP.

## Core value proposition
MedGuard AI answers three questions:

1. **What is likely to run out?**
2. **What is likely to expire?**
3. **What should we reorder and when?**

## Architecture

```text
React Dashboard
      |
      v
FastAPI Backend
      |
  +---+---+
  |       |
Inventory  ML Forecasting
  |       |
  +---+---+
      |
 inventory.csv
```

## Run locally

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://localhost:8000`

### Frontend
Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Hackathon upgrade priorities

The included ML endpoint is a deliberately simple MVP. During the 24-hour event, replace its synthetic history with real historical demand data and add:

- time-series lag/rolling features
- model evaluation (MAE/RMSE)
- expiry-risk scoring
- supplier lead-time-aware reorder quantity
- authentication
- PostgreSQL/Supabase persistence
- charts and downloadable reports
- an AI natural-language inventory assistant

## Demo scenario

Use these questions in your presentation:

> “Which medicine is at highest stock-out risk?”

> “How much Paracetamol should we order for the next 14 days?”

> “Which medicines should be prioritized before expiry?”

## Important

This is a **hackathon decision-support prototype**, not a clinical decision-making system. Predictions should be validated against real inventory and demand data before operational use.
