from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path
import threading

app = FastAPI(title="MedGuard AI API", version="1.1.0")

# FIX: allow_credentials must be False when allow_origins=["*"] (CORS spec).
# Browser blocks credentialed requests to a wildcard origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FIX: __file__ is backend/app/main.py
#   .parent        -> backend/app
#   .parent.parent -> backend
# so this correctly resolves to backend/data/inventory.csv
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.csv"

# FIX: lock + atomic write so concurrent POSTs don't corrupt the CSV.
_write_lock = threading.Lock()

# FIX: one constant for reorder horizon so /api/inventory and /api/forecast agree.
REORDER_HORIZON_DAYS = 14


class Medicine(BaseModel):
    name: str
    category: str
    quantity: int = Field(ge=0)
    daily_usage: float = Field(ge=0)
    reorder_level: int = Field(ge=0)
    expiry_date: str

    # FIX: reject malformed dates at request time instead of 500-ing later.
    @field_validator("expiry_date")
    @classmethod
    def _valid_date(cls, v: str) -> str:
        try:
            pd.to_datetime(v)
        except Exception:
            raise ValueError(f"expiry_date '{v}' is not a valid date")
        return v


def _safe_usage(x) -> float:
    """FIX: single handler for NaN / zero / negative daily_usage."""
    if pd.isna(x) or x <= 0:
        return 0.1
    return float(x)


def load_inventory() -> pd.DataFrame:
    # FIX: explicit error with the resolved path instead of a cryptic 500.
    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Inventory CSV not found at {DATA_PATH}",
        )
    df = pd.read_csv(DATA_PATH)
    # FIX: normalize daily_usage once so every downstream calc agrees.
    df["daily_usage"] = df["daily_usage"].apply(_safe_usage)
    return df


def risk_level(row) -> str:
    # Uses the already-normalized daily_usage from load_inventory().
    days_left = row["quantity"] / row["daily_usage"]
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
    df["days_of_stock"] = (df["quantity"] / df["daily_usage"]).round(1)
    df["risk"] = df.apply(risk_level, axis=1)
    df["recommended_order"] = (
        (df["daily_usage"] * REORDER_HORIZON_DAYS - df["quantity"])
        .clip(lower=0)
        .round()
        .astype(int)
    )
    return df.to_dict(orient="records")


@app.get("/api/summary")
def summary():
    df = load_inventory()
    risks = df.apply(risk_level, axis=1)

    # FIX: errors="coerce" so one bad date doesn't 500 the whole endpoint.
    expiry = pd.to_datetime(df["expiry_date"], errors="coerce")
    expiring_30_days = int(
        (expiry - pd.Timestamp.today()).dt.days.le(30).sum()
    )

    return {
        "total_medicines": int(len(df)),
        "critical": int((risks == "Critical").sum()),
        "high": int((risks == "High").sum()),
        "expiring_30_days": expiring_30_days,
        "total_units": int(df["quantity"].sum()),
    }


@app.get("/api/forecast/{medicine}")
def forecast(medicine: str, days: int = 7):
    df = load_inventory()
    row = df[df["name"].str.lower() == medicine.lower()]

    # FIX: proper 404 instead of 200-with-error-body.
    if row.empty:
        raise HTTPException(status_code=404, detail="Medicine not found")

    r = row.iloc[0]

    # NOTE: this is a demo baseline. The model sees only a time index against
    # i.i.d. synthetic noise, so it effectively predicts the mean of `hist`
    # (~ daily_usage). It is not making real predictions. Replace `hist` with
    # genuine historical sales data and add lag/rolling features before
    # treating output as real forecasting.
    rng = np.random.default_rng(42)
    base = float(r["daily_usage"])
    hist = np.maximum(1, rng.normal(base, max(base * 0.12, 1), 30))

    X = np.arange(30).reshape(-1, 1)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, hist)

    future_X = np.arange(30, 30 + days).reshape(-1, 1)
    predictions = np.maximum(0, model.predict(future_X))
    predicted_total = float(predictions.sum())

    return {
        "medicine": r["name"],
        "days": days,
        "predicted_daily_demand": [round(float(x), 1) for x in predictions],
        "predicted_total_demand": round(predicted_total, 1),
        "current_stock": int(r["quantity"]),
        "recommended_order": int(max(0, np.ceil(predicted_total - r["quantity"]))),
    }


@app.post("/api/inventory")
def add_medicine(medicine: Medicine):
    # FIX: lock + atomic temp-file rename so concurrent writes can't corrupt CSV.
    with _write_lock:
        df = load_inventory()
        new_row = pd.DataFrame([medicine.model_dump()])
        df = pd.concat([df, new_row], ignore_index=True)

        tmp = DATA_PATH.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        tmp.replace(DATA_PATH)

    return {"message": "Medicine added", "medicine": medicine.model_dump()}

