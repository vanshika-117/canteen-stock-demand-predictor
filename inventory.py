"""Core data validation and stock recommendation logic."""
from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import IO, Union

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "date", "item", "units_sold", "opening_stock",
    "stock_received", "closing_stock"
]
DataSource = Union[str, Path, IO]


def load_and_validate_data(source: DataSource) -> tuple[pd.DataFrame, list[str]]:
    """Load CSV and validate required fields and inventory arithmetic."""
    df = pd.read_csv(source)
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    if df.empty:
        return df, []

    if df.isnull().any().any():
        raise ValueError("Blank cells are not allowed. Enter 0 for zero sales or zero stock received.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("One or more dates are invalid. Use YYYY-MM-DD.")

    df["item"] = df["item"].astype(str).str.strip()
    if (df["item"] == "").any():
        raise ValueError("Item names cannot be blank.")

    numeric = ["units_sold", "opening_stock", "stock_received", "closing_stock"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            raise ValueError(f"{col} must contain numeric values.")
        if (df[col] < 0).any():
            raise ValueError(f"{col} cannot contain negative quantities.")

    if not np.all(np.equal(np.mod(df[numeric].to_numpy(), 1), 0)):
        raise ValueError("Quantities must be whole numbers.")

    if df.duplicated(["date", "item"]).any():
        raise ValueError("Duplicate date/item rows found. Keep one row per item per day.")

    expected = df["opening_stock"] + df["stock_received"] - df["units_sold"]
    if not expected.equals(df["closing_stock"]):
        mismatch = df.loc[expected != df["closing_stock"], ["date", "item"]].head(5)
        details = ", ".join(f"{r.date.date()} / {r.item}" for r in mismatch.itertuples())
        raise ValueError(
            "Stock reconciliation failed: opening_stock + stock_received - "
            f"units_sold must equal closing_stock. Check: {details}"
        )

    warnings = []
    if len(df) < 20:
        warnings.append(f"Only {len(df)} records found. The assignment requires at least 20 real entries.")
    if df["date"].nunique() < 3:
        warnings.append("Fewer than 3 distinct dates: forecasts will be highly uncertain.")
    return df.sort_values(["item", "date"]).reset_index(drop=True), warnings


def build_recommendations(data: pd.DataFrame, safety_factor: float = 1.0) -> pd.DataFrame:
    """Forecast next-day demand from recent observations and estimate reorder quantity."""
    if not 0 <= safety_factor <= 2.5:
        raise ValueError("safety_factor must be between 0 and 2.5.")
    if data.empty:
        return pd.DataFrame(columns=[
            "item", "forecast_demand", "safety_stock",
            "available_stock", "suggested_order"
        ])

    rows = []
    for item, group in data.groupby("item"):
        group = group.sort_values("date")
        recent = group.tail(7)["units_sold"].astype(float)
        all_sales = group["units_sold"].astype(float)

        recent_mean = float(recent.mean())
        overall_mean = float(all_sales.mean())
        forecast = 0.7 * recent_mean + 0.3 * overall_mean
        variability = float(recent.std(ddof=1)) if len(recent) > 1 else 0.0
        buffer = ceil(safety_factor * variability)
        available = int(group.iloc[-1]["closing_stock"])
        order = max(0, ceil(forecast + buffer - available))

        rows.append({
            "item": item,
            "forecast_demand": round(forecast, 2),
            "safety_stock": buffer,
            "available_stock": available,
            "suggested_order": order,
        })

    return pd.DataFrame(rows).sort_values(
        ["suggested_order", "forecast_demand"], ascending=[False, False]
    ).reset_index(drop=True)
