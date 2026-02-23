import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Alcohol Tracker Game", layout="centered")

# -----------------------------
# USER SETUP
# -----------------------------
USERS = ["Tim", "Rareș", "Rebecca"]

user = st.selectbox("Who is using the app?", USERS)
filename = f"data/{user}.csv"

os.makedirs("data", exist_ok=True)
if not os.path.exists(filename):
    pd.DataFrame(columns=["date", "drink_type", "volume", "abv", "units", "drinks"]).to_csv(filename, index=False)

# -----------------------------
# INSTRUCTIONS
# -----------------------------
st.markdown("""
### How scoring works
- **0 units = 100 points**
- **Each unit = −10 points**
- **Each drink = −2 points**
- **Negative scores are possible**
- **Highest score wins the day**
- **Weekly score = sum of the last 7 days**

### How to win
- Log drinks honestly  
- Use **“0 alcohol today”** to claim a sober day  
- Keep your weekly score higher than your friends  
- Check the leaderboard to see who’s ahead  
""")

# -----------------------------
# FUNCTIONS
# -----------------------------
def calculate_units(volume, abv):
    return volume * (abv / 100) * 0.789

def calculate_score(units, drinks):
    if units == 0:
        return 100
    return 100 - (10 * units) - (2 * drinks)

def load_user_df(u):
    f = f"data/{u}.csv"
    if not os.path.exists(f):
        return pd.DataFrame(columns=["date", "drink_type", "volume", "abv", "units", "drinks"])
    return pd.read_csv(f)

def get_last_logged_score(df):
    if df.empty:
        return None
    last_row = df.iloc[-1]
    return calculate_score(last_row["units"], last_row["drinks"])

# -----------------------------
# LOGGING SECTION
# -----------------------------
st.header("Log your drinks")

drink_type = st.text_input("Drink type (Beer, Wine, etc.)")
volume = st.number_input("Volume (ml)", min_value=0.0)
abv = st.number_input("ABV (%)", min_value=0.0)

if st.button("Add drink"):
    units = calculate_units(volume, abv)
    new_row = {
        "date": datetime.now().date(),
        "drink_type": drink_type,
        "volume": volume,
        "abv": abv,
        "units": units,
        "drinks": 1
    }
    df = load_user_df(user)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(filename, index=False)
    st.success("Drink added!")

if st.button("0 alcohol today"):
    new_row = {
        "date": datetime.now().date(),
        "drink_type": "None",
        "volume": 0,
        "abv": 0,
        "units": 0,
        "drinks": 0
    }
    df = load_user_df(user)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(filename, index=False)
    st.success("Logged a sober day!")

# -----------------------------
# DAILY LEADERBOARD
# -----------------------------
st.header("Daily Leaderboard")

today = datetime.now().date()
daily_data = []

for u in USERS:
    df = load_user_df(u)
    today_df = df[df["date"] == str(today)]

    units_today = today_df["units"].sum() if not today_df.empty else 0
    drinks_today = today_df["drinks"].sum() if not today_df.empty else 0
    score_today = calculate_score(units_today, drinks_today)

    last_score = get_last_logged_score(df[df["date"] != str(today)])
    if last_score is None:
        trend = "—"
    else:
        if score_today > last_score:
            trend = "↑"
        elif score_today < last_score:
            trend = "↓"
            trend = "↓"
        else:
            trend = "→"

    daily_data.append([u, units_today, drinks_today, round(score_today, 1), trend])

daily_df = pd.DataFrame(daily_data, columns=["User", "Units", "Drinks", "Score", "Trend"])
daily_df = daily_df.sort_values(by="Score", ascending=False)
st.table(daily_df)

# -----------------------------
# WEEKLY LEADERBOARD
# -----------------------------
st.header("Weekly Leaderboard")

week_ago = today - timedelta(days=7)
weekly_data = []

for u in USERS:
    df = load_user_df(u)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    week_df = df[df["date"] >= week_ago]

    units_week = week_df["units"].sum()
    drinks_week = week_df["drinks"].sum()

    # compute weekly score
    daily_scores = []
    for d in week_df["date"].unique():
        day_df = week_df[week_df["date"] == d]
        units_d = day_df["units"].sum()
        drinks_d = day_df["drinks"].sum()
        daily_scores.append(calculate_score(units_d, drinks_d))

    weekly_score = sum(daily_scores) if daily_scores else 0

    weekly_data.append([u, round(units_week, 1), drinks_week, round(weekly_score, 1)])

weekly_df = pd.DataFrame(weekly_data, columns=["User", "Units (7d)", "Drinks (7d)", "Score (7d)"])
weekly_df = weekly_df.sort_values(by="Score (7d)", ascending=False)
st.table(weekly_df)

# -----------------------------
# AUDIT LINK
# -----------------------------
st.markdown("""
### Check your drinking habits
Take the official AUDIT alcohol screening test:  
https://auditscreen.org/check-your-drinking/
""")
