from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path
import threading

app = FastAPI(title="MedGuard AI API", version="1.2.0")

# CORS: allow_credentials must be False when allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths: __file__ = backend/app/main.py → .parent.parent = backend/
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
DATA_PATH  = DATA_DIR / "inventory.csv"
BEDS_PATH  = DATA_DIR / "beds.csv"
STAFF_PATH = DATA_DIR / "staff.csv"

# Lock + atomic write to prevent CSV corruption under concurrent POSTs.
_write_lock = threading.Lock()

# Single reorder horizon so /api/inventory and /api/forecast agree.
REORDER_HORIZON_DAYS = 14

# Redistribution thresholds.
DEFICIT_DAYS = 7    # below this → deficit
SURPLUS_DAYS = 21   # above this → surplus


class Medicine(BaseModel):
    facility_id: str
    facility_name: str
    district: str
    name: str
    category: str
    quantity: int = Field(ge=0)
    daily_usage: float = Field(ge=0)
    reorder_level: int = Field(ge=0)
    expiry_date: str

    @field_validator("expiry_date")
    @classmethod
    def _valid_date(cls, v: str) -> str:
        try:
            pd.to_datetime(v)
        except Exception:
            raise ValueError(f"expiry_date '{v}' is not a valid date")
        return v


def _safe_usage(x) -> float:
    """Handle NaN / zero / negative daily_usage."""
    if pd.isna(x) or x <= 0:
        return 0.1
    return float(x)


def load_inventory() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Inventory CSV not found at {DATA_PATH}",
        )
    df = pd.read_csv(DATA_PATH)
    df["daily_usage"] = df["daily_usage"].apply(_safe_usage)
    return df


def risk_level(row) -> str:
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


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@app.get("/api/inventory")
def inventory(facility_id: str | None = None):
    df = load_inventory()
    if facility_id:
        df = df[df["facility_id"] == facility_id]
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Facility '{facility_id}' not found",
            )
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
def summary(facility_id: str | None = None):
    df = load_inventory()
    if facility_id:
        df = df[df["facility_id"] == facility_id]
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Facility '{facility_id}' not found",
            )

    risks = df.apply(risk_level, axis=1)

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


# ---------------------------------------------------------------------------
# Facilities (national network view)
# ---------------------------------------------------------------------------

@app.get("/api/facilities")
def facilities():
    df = load_inventory()
    grouped = (
        df.groupby(["facility_id", "facility_name", "district"], as_index=False)
        .agg(
            total_items=("name", "count"),
            total_units=("quantity", "sum"),
        )
    )
    return grouped.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Beds
# ---------------------------------------------------------------------------

@app.get("/api/beds")
def beds():
    if not BEDS_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Beds CSV not found at {BEDS_PATH}",
        )
    df = pd.read_csv(BEDS_PATH)
    df["occupancy_pct"] = (df["occupied_beds"] / df["total_beds"] * 100).round(1)
    df["available_beds"] = df["total_beds"] - df["occupied_beds"]
    df["status"] = np.select(
        [df["occupancy_pct"] >= 95, df["occupancy_pct"] >= 80],
        ["Critical", "High"],
        default="Normal",
    )
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

@app.get("/api/staff")
def staff():
    if not STAFF_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Staff CSV not found at {STAFF_PATH}",
        )
    df = pd.read_csv(STAFF_PATH)
    df["attendance_pct"] = (df["present"] / df["total"] * 100).round(1)
    df["status"] = np.select(
        [df["attendance_pct"] < 60, df["attendance_pct"] < 80],
        ["Critical", "Low"],
        default="Normal",
    )
    return df.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Cross-district redistribution
# ---------------------------------------------------------------------------

@app.get("/api/redistribution")
def redistribution():
    """Recommend cross-facility medicine transfers to cover deficits.

    Deficit  = a facility with fewer than DEFICIT_DAYS days of stock.
    Surplus  = a facility with more than SURPLUS_DAYS days of the same medicine.
    Transfer = enough to bring the deficit facility to 14 days,
               capped at what the source can spare above its SURPLUS_DAYS buffer.
    """
    df = load_inventory()
    df["days_of_stock"] = (df["quantity"] / df["daily_usage"]).round(1)

    surplus = df[df["days_of_stock"] > SURPLUS_DAYS].copy()
    deficit = df[df["days_of_stock"] < DEFICIT_DAYS].copy()

    recommendations = []
    for _, d in deficit.iterrows():
        candidates = surplus[surplus["name"] == d["name"]]
        if candidates.empty:
            continue
        source = candidates.sort_values("days_of_stock", ascending=False).iloc[0]

        needed = int(d["daily_usage"] * 14 - d["quantity"])
        spare = int(source["quantity"] - source["daily_usage"] * SURPLUS_DAYS)
        transfer = max(0, min(needed, spare))

        if transfer > 0:
            recommendations.append({
                "medicine": d["name"],
                "from_facility_id": source["facility_id"],
                "from_facility": source["facility_name"],
                "from_district": source["district"],
                "to_facility_id": d["facility_id"],
                "to_facility": d["facility_name"],
                "to_district": d["district"],
                "transfer_units": transfer,
                "reason": (
                    f"{d['facility_name']} has {d['days_of_stock']} days left; "
                    f"{source['facility_name']} has {source['days_of_stock']} days"
                ),
            })

    return recommendations


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

@app.get("/api/forecast/{medicine}")
def forecast(medicine: str, days: int = 7, facility_id: str | None = None):
    df = load_inventory()
    matches = df[df["name"].str.lower() == medicine.lower()]
    if facility_id:
        matches = matches[matches["facility_id"] == facility_id]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Medicine '{medicine}' not found"
            + (f" at facility '{facility_id}'" if facility_id else ""),
        )

    r = matches.iloc[0]

    # Demo baseline: the model sees only a time index against i.i.d. synthetic
    # noise, so it predicts roughly the mean of `hist`. Not real forecasting.
    # Replace with genuine historical sales data and lag/rolling features.
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
        "facility_id": r["facility_id"],
        "facility_name": r["facility_name"],
        "days": days,
        "predicted_daily_demand": [round(float(x), 1) for x in predictions],
        "predicted_total_demand": round(predicted_total, 1),
        "current_stock": int(r["quantity"]),
        "recommended_order": int(max(0, np.ceil(predicted_total - r["quantity"]))),
    }


# ---------------------------------------------------------------------------
# Add medicine
# ---------------------------------------------------------------------------

@app.post("/api/inventory")
def add_medicine(medicine: Medicine):
    with _write_lock:
        df = load_inventory()
        new_row = pd.DataFrame([medicine.model_dump()])
        df = pd.concat([df, new_row], ignore_index=True)

        tmp = DATA_PATH.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        tmp.replace(DATA_PATH)

    return {"message": "Medicine added", "medicine": medicine.model_dump()}

