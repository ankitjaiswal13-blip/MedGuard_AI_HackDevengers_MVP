# 🏥 MedGuard AI

### AI-Powered Medicine Inventory & Demand Forecasting System

> **Predict. Prevent. Protect.**

MedGuard AI is an intelligent medicine inventory management system designed to help hospitals, pharmacies, and healthcare inventory managers monitor medicine stock, identify inventory risks, forecast future demand, and make smarter reorder decisions.

---

## 🚀 Problem Statement

Medicine inventory management is often dependent on manual tracking and basic stock-level monitoring.

This can lead to:

- ❌ Unexpected medicine stock-outs
- ❌ Overstocking and unnecessary expenses
- ❌ Medicine expiry and wastage
- ❌ Difficulty predicting future demand
- ❌ Slow and inefficient inventory decisions

MedGuard AI addresses these challenges using inventory analytics and machine-learning-based demand forecasting.

---

## 💡 Our Solution

MedGuard AI provides a centralized dashboard that converts inventory data into actionable recommendations.

### Core workflow

```text
Medicine Inventory
       ↓
Inventory Analysis
       ↓
Risk Detection
       ↓
Demand Forecasting
       ↓
Smart Reorder Recommendation
       ↓
Better Inventory Decisions

✨ Key Features
📦 Inventory Management

Track important information for every medicine:

Medicine name
Category
Current quantity
Daily usage
Reorder level
Expiry date
⚠️ Inventory Risk Detection

MedGuard AI analyzes current inventory and identifies medicines requiring attention.

Risk levels include:

🟢 Low
🟡 Medium
🟠 High
🔴 Critical
🤖 AI Demand Forecasting

The system generates a 7-day demand forecast for individual medicines.

The forecast provides:

Current stock
Predicted daily demand
Predicted 7-day demand
Recommended order quantity
🛒 Smart Reorder Recommendation

Instead of simply saying that stock is low, MedGuard AI recommends how many units should be ordered.

Example:

Medicine: Paracetamol 500mg

Current Stock:        120 units
Predicted Demand:     183.5 units
Recommended Order:     64 units
Risk:                  High
📊 Interactive Dashboard

The dashboard provides a quick overview of:

Total medicines
Critical medicines
High-risk medicines
Expiring medicines
Inventory risk
Reorder recommendations
Demand forecasts
🧠 AI / ML Approach

The project uses Python-based data processing and machine learning to estimate future medicine demand.

Current MVP

The forecasting layer uses:

Python
Pandas
NumPy
Scikit-learn
Random Forest Regression

The system generates demand predictions and compares them with current inventory to calculate recommended reorder quantities.

Future improvement

The forecasting model can be improved using real historical sales/inventory data with:

Lag features
Rolling averages
Seasonal patterns
Supplier lead time
Historical demand trends
Model evaluation using MAE/RMSE
More advanced time-series models
🏗️ System Architecture
                 ┌──────────────────────┐
                 │   React Dashboard     │
                 │      Frontend         │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    FastAPI Backend   │
                 │        REST API      │
                 └──────────┬───────────┘
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
          ┌──────────────┐    ┌──────────────┐
          │  Inventory   │    │  ML Forecast │
          │    Data      │    │    Engine    │
          └──────────────┘    └──────────────┘
                  │                   │
                  └─────────┬─────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Smart Recommendations│
                 └──────────────────────┘
🛠️ Technology Stack
Frontend
React
Vite
CSS
Backend
Python
FastAPI
Uvicorn
AI / Machine Learning
Pandas
NumPy
Scikit-learn
Random Forest Regression
Data
CSV-based inventory dataset for the MVP

📁 Project Structure

MedGuard_AI_HackDevengers_MVP/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── data/
│   │   └── inventory.csv
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   │
│   ├── index.html
│   └── package.json
│
├── README.md
└── .gitignore
⚙️ Installation & Setup
1. Clone the repository
git clone https://github.com/ankitjaiswal13-blip/MedGuard_AI_HackDevengers_MVP.git
cd MedGuard_AI_HackDevengers_MVP
🔧 Backend Setup

Go to the backend directory:

cd backend

Create a virtual environment:

python -m venv .venv

Activate it.

Windows PowerShell
.venv\Scripts\Activate.ps1

Install dependencies:

python -m pip install -r requirements.txt

Start the FastAPI server:

python -m uvicorn app.main:app --reload --port 8000

Backend:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs
🎨 Frontend Setup

Open another terminal.

Go to the frontend:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

Frontend:

http://localhost:5173/
🔌 API Endpoints
Health Check
GET /

Checks whether the backend is running.

Get Inventory
GET /api/inventory

Returns medicine inventory information including risk and recommended order quantity.

Add Medicine
POST /api/inventory

Adds a new medicine to the inventory.

Example:

{
  "name": "Paracetamol",
  "category": "Tablet",
  "quantity": 100,
  "daily_usage": 10,
  "reorder_level": 20,
  "expiry_date": "2027-12-31"
}
Get Forecast
GET /api/forecast/{medicine}?days=7

Generates a demand forecast for the selected medicine.

Example:

/api/forecast/Paracetamol%20500mg?days=7
📊 Example Output

For a medicine such as Paracetamol:

Current Stock
     ↓
120 units

Predicted 7-Day Demand
     ↓
183.5 units

Recommended Order
     ↓
64 units

This allows an inventory manager to take action before a stock-out occurs.

🎯 Target Users

MedGuard AI can support:

🏥 Hospitals
💊 Pharmacies
🏪 Medical stores
🏬 Healthcare supply centers
📦 Medical inventory managers
🌍 Potential Impact

MedGuard AI aims to help healthcare organizations:

Reduce stock-out risk
Reduce medicine wastage
Improve inventory planning
Make faster inventory decisions
Better anticipate medicine demand
Improve availability of essential medicines
🔮 Future Scope

The MVP can be expanded with:

🗄️ Real Database

Move from CSV storage to:

PostgreSQL
Supabase
Firebase
📈 Advanced Forecasting

Use real historical medicine demand data and evaluate models using:

MAE
RMSE
MAPE
🚚 Supplier Intelligence

Consider:

Supplier lead time
Supplier reliability
Purchase price
Minimum order quantity

🌐 Multi-Location Inventory

Allow hospitals/pharmacies to manage inventory across multiple locations.

🧠 AI Inventory Assistant

Allow users to ask:

Which medicines are at high stock-out risk?
What should we reorder this week?
Which medicines are approaching expiry?

⚠️ Disclaimer

MedGuard AI is a hackathon prototype and inventory decision-support system.

Its predictions should be validated against real operational inventory and demand data before being used in real healthcare operations.

It is not intended to replace clinical judgment or professional healthcare decision-making.

👨‍💻 Project

MedGuard AI

Built for:

Hack Devengers 2.0

Repository

https://github.com/ankitjaiswal13-blip/MedGuard_AI_HackDevengers_MVP

⭐ Project Vision

Don't wait for medicines to run out. Predict what healthcare needs next.

MedGuard AI — Predict. Prevent. Protect.

## 👨‍💻 Team / Developer

**Ankit Jaiswal**  
ECE Student  
Project: **MedGuard AI**

### GitHub
https://github.com/ankitjaiswal13-blip

### Project Repository
https://github.com/ankitjaiswal13-blip/MedGuard_AI_HackDevengers_MVP
