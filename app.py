from pathlib import Path
import pandas as pd
import streamlit as st
from inventory import load_and_validate_data, build_recommendations, REQUIRED_COLUMNS

DATA_PATH = Path(__file__).parent / "data.csv"

st.set_page_config(page_title="Canteen Stock & Demand Predictor", page_icon="🥪", layout="wide")
st.title("🥪 Canteen Stock & Demand Predictor")
st.caption("A data-driven stock planning assistant for a college canteen.")

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload your collected CSV", type=["csv"])
    st.caption("Use real observations collected at your canteen. Do not use generated or sample records.")
    safety_factor = st.slider("Safety-stock factor", min_value=0.0, max_value=2.5, value=1.0, step=0.1)
    st.caption("Higher values keep a larger buffer. This is a planning aid, not an automatic purchase order.")

try:
    source = uploaded if uploaded is not None else DATA_PATH
    if not source.exists() if isinstance(source, Path) else False:
        st.warning("No data.csv found yet. Collect real canteen records, fill the provided template, and place it beside app.py.")
        st.code(",".join(REQUIRED_COLUMNS))
        st.stop()

    data, warnings = load_and_validate_data(source)
    for warning in warnings:
        st.warning(warning)

    if data.empty:
        st.info("The CSV is valid but contains no observations yet. Add at least 20 genuine item-day records to generate recommendations.")
        st.stop()

    st.subheader("Inventory overview")
    latest_date = data["date"].max()
    st.write(f"Latest recorded date: **{latest_date.date()}**")
    recommendations = build_recommendations(data, safety_factor=safety_factor)

    c1, c2, c3 = st.columns(3)
    c1.metric("Items tracked", int(recommendations["item"].nunique()))
    c2.metric("Total available stock", int(recommendations["available_stock"].sum()))
    c3.metric("Items to reorder", int((recommendations["suggested_order"] > 0).sum()))

    st.subheader("Next-day stock recommendations")
    display = recommendations.rename(columns={
        "item": "Item", "forecast_demand": "Forecast demand",
        "safety_stock": "Safety stock", "available_stock": "Available stock",
        "suggested_order": "Suggested order"
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("Demand history")
    chart_data = data.pivot_table(index="date", columns="item", values="units_sold", aggfunc="sum").fillna(0)
    st.line_chart(chart_data)

    st.subheader("Stock planning notes")
    st.markdown(
        "- Forecasts use observed sales, not external APIs or downloaded datasets.\n"
        "- Each item should have a row for each day observed; enter zero when there were no sales.\n"
        "- The latest closing stock is treated as the stock currently available.\n"
        "- Review supplier lead times, perishability and upcoming events before ordering."
    )
    st.download_button(
        "Download recommendations as CSV",
        recommendations.to_csv(index=False).encode("utf-8"),
        file_name="stock_recommendations.csv",
        mime="text/csv"
    )
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not process the data: {exc}")
    st.info("Check the CSV headers, dates, numeric quantities and stock reconciliation.")
