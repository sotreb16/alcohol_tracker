import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.calculations import calculate_units
from utils.audit_c import audit_c_score, audit_c_risk
from utils.charts import weekly_units_chart, daily_units_chart

st.set_page_config(page_title="Alcohol Tracker", layout="wide")

# Load or create data
try:
    df = pd.read_csv("data/drinks.csv", parse_dates=["date"])
except:
    df = pd.DataFrame(columns=["date", "type", "volume_ml", "abv", "units", "craving", "notes"])

st.title("Alcohol Tracker (Local Only)")

st.header("Log a drink")
col1, col2, col3 = st.columns(3)

drink_type = col1.selectbox("Type", ["Beer", "Wine", "Spirits"])
volume = col2.number_input("Volume (ml)", 0, 2000, 330)
abv = col3.number_input("ABV (%)", 0.0, 80.0, 5.0)

craving = st.slider("Craving (1–10)", 1, 10, 5)
notes = st.text_input("Notes")

if st.button("Add entry"):
    units = calculate_units(volume, abv)
    new_row = {
        "date": datetime.now(),
        "type": drink_type,
        "volume_ml": volume,
        "abv": abv,
        "units": units,
        "craving": craving,
        "notes": notes
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv("data/drinks.csv", index=False)
    st.success("Logged!")

st.header("Analytics")

if len(df) > 0:
    st.plotly_chart(daily_units_chart(df), use_container_width=True)
    st.plotly_chart(weekly_units_chart(df), use_container_width=True)

    st.subheader("Dry-day streak")
    streak = (df.groupby(df["date"].dt.date)["units"].sum() == 0).astype(int)
    st.write(f"Current streak: {streak[::-1].cumsum().iloc[0]} days")

st.header("AUDIT‑C Screening")
q1 = st.selectbox("How often do you drink?", ["Never", "Monthly", "Weekly", "Daily"])
q2 = st.selectbox("How many drinks on a typical day?", ["1–2", "3–4", "5–6", "7+"])
q3 = st.selectbox("How often 6+ drinks?", ["Never", "Monthly", "Weekly", "Daily"])

score = audit_c_score(q1, q2, q3)
risk = audit_c_risk(score)

st.write(f"Score: **{score}** — {risk}")
