from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path

app = FastAPI(title="MedGuard AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.csv"

class Medicine(BaseModel):
    name: str
    category: str
    quantity: int
    daily_usage: float
    reorder_level: int
    expiry_date: str

def load_inventory():
    return pd.read_csv(DATA_PATH)

def risk_level(row):
    days_left = row["quantity"] / max(row["daily_usage"], 0.1)
    if days_left < 3 or row["quantity"] <= row["reorder_level"]:
        return "Critical"
    if days_left < 7 or row["quantity"] <= row["reorder_level"] * 1.5:
        return "High"
    if days_left < 14:
        return "Medium"
    return "Low"

@app.get("/")
def root():
    return {"message": "MedGuard AI API is running"}

@app.get("/api/inventory")
def inventory():
    df = load_inventory()
    df["days_of_stock"] = (df["quantity"] / df["daily_usage"].clip(lower=0.1)).round(1)
    df["risk"] = df.apply(risk_level, axis=1)
    df["recommended_order"] = (
        (df["daily_usage"] * 14 - df["quantity"]).clip(lower=0).round().astype(int)
    )
    return df.to_dict(orient="records")

@app.get("/api/summary")
def summary():
    df = load_inventory()
    df["days_of_stock"] = df["quantity"] / df["daily_usage"].clip(lower=0.1)
    risks = df.apply(risk_level, axis=1)
    return {
        "total_medicines": int(len(df)),
        "critical": int((risks == "Critical").sum()),
        "high": int((risks == "High").sum()),
        "expiring_30_days": int((pd.to_datetime(df["expiry_date"]) - pd.Timestamp.today()).dt.days.le(30).sum()),
        "total_units": int(df["quantity"].sum()),
    }

@app.get("/api/forecast/{medicine}")
def forecast(medicine: str, days: int = 7):
    df = load_inventory()
    row = df[df["name"].str.lower() == medicine.lower()]
    if row.empty:
        return {"error": "Medicine not found"}

    r = row.iloc[0]
    # Demo forecasting model: synthetic historical demand based on current usage.
    # Replace with real historical sales data during the hackathon.
    rng = np.random.default_rng(42)
    base = float(r["daily_usage"])
    hist = np.maximum(1, rng.normal(base, max(base * 0.12, 1), 30))
    X = np.arange(30).reshape(-1, 1)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, hist)
    future_X = np.arange(30, 30 + days).reshape(-1, 1)
    predictions = np.maximum(0, model.predict(future_X))
    return {
        "medicine": r["name"],
        "days": days,
        "predicted_daily_demand": [round(float(x), 1) for x in predictions],
        "predicted_total_demand": round(float(predictions.sum()), 1),
        "current_stock": int(r["quantity"]),
        "recommended_order": int(max(0, np.ceil(predictions.sum() - r["quantity"]))),
    }

@app.post("/api/inventory")
def add_medicine(medicine: Medicine):
    df = load_inventory()
    new_row = pd.DataFrame([medicine.model_dump()])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    return {"message": "Medicine added", "medicine": medicine.model_dump()}
