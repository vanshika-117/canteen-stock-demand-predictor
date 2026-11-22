# Canteen Stock & Demand Predictor

A small inventory-planning tool for a college canteen. It reads first-hand item/day records from CSV, validates stock arithmetic, estimates next-day demand and calculates a suggested reorder quantity.

## Why this exists
[Replace with the real place, observation date and the person/role you spoke with. Do not publish a person's name or photo without permission.]

## Features
- CSV ingestion and strict validation
- Duplicate and invalid quantity detection
- Stock reconciliation: opening + received - sold = closing
- Recent-demand forecast blended with historical average
- Variability-based safety-stock buffer
- Per-item reorder recommendation
- Interactive Streamlit dashboard and CSV export
- Automated unit tests

## Data format
One row per item per date. Record zero sales as `0`; do not omit a day just because an item did not sell.

| Column | Meaning |
|---|---|
| date | YYYY-MM-DD |
| item | Item name |
| units_sold | Units sold that day |
| opening_stock | Units available at start of day |
| stock_received | Units added during day |
| closing_stock | Units remaining at end of day |

The reconciliation rule is `opening_stock + stock_received - units_sold = closing_stock`.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Put your collected `data.csv` beside `app.py`, or upload it in the sidebar.

## Run tests
```bash
pytest -q
```

## Forecast logic
For each item:
- Recent average = mean of the latest 7 recorded daily observations.
- Historical average = mean of all recorded daily observations.
- Forecast = 70% recent average + 30% historical average.
- Safety stock = ceiling(safety factor × sample standard deviation of recent demand).
- Suggested order = max(0, ceiling(forecast + safety stock − latest closing stock)).

The safety factor is configurable in the sidebar. This is a simple, explainable heuristic, not a trained machine-learning model.

## Real output
[After running on your genuine data, paste the generated recommendation table here or attach a screenshot. Never use illustrative/fabricated figures as actual output.]

## What it gets wrong / limitations
- Assumes recorded sales are a reasonable proxy for demand; stockouts can hide unmet demand.
- Does not account for supplier lead time, holidays, events, weather, price changes or perishability.
- Requires consistent daily records, including zero-sales days.
- Uses a small-history heuristic; forecasts are uncertain with limited observations.
- The latest closing stock is assumed to be the current available stock.

## Fieldwork
[Add visit date, exact location, collection method and interview summary. Add two timestamped fieldwork photos only with appropriate permission.]

## Demo video
[Add a shareable link to your 3-minute screen recording.]

## AI use
AI assistance was used for [truthfully describe research/coding/debugging]. The exported conversation(s) used during this work are in `ai-chats/`.

## Repository
[Add public GitHub URL after pushing.]
