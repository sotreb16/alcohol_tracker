import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Alcohol Tracker Game", layout="centered")

# -----------------------------
# CUSTOM CSS (gradient, orange theme, gold/silver/bronze rows)
# -----------------------------
st.markdown("""
<style>

/* Gradient background */
body {
    background: linear-gradient(135deg, #f2f2f2 0%, #e6e6e6 100%) !important;
}

/* Main container spacing */
.block-container {
    padding-top: 2rem;
}

/* Headings in warm orange */
h1, h2, h3, h4 {
    color: #FF8C42 !important;
}

/* Buttons */
.stButton>button {
    background-color: #FF8C42 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    border: none !important;
    font-weight: 600 !important;
}

.stButton>button:hover {
    background-color: #ffa766 !important;
}

/* Leaderboard table styling */
table {
    border-collapse: collapse;
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
}

thead tr th {
    background-color: #FF8C42 !important;
    color: white !important;
    padding: 10px;
    font-size: 1rem;
}

tbody tr:nth-child(even) {
    background-color: #fafafa;
}

tbody tr:nth-child(odd) {
    background-color: #ffffff;
}

tbody tr:hover {
    background-color: #ffe8d6 !important;
}

/* Gold / Silver / Bronze rows */
tr.gold-row {
    background-color: #FFD700 !important;
}

tr.silver-row {
    background-color: #C0C0C0 !important;
}

tr.bronze-row {
    background-color: #CD7F32 !important;
}

/* Make emojis larger */
td {
    font-size: 1.1rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# USER SETUP
# -----------------------------
USERS = ["Tim", "Rareș", "Rebecca"]

# Emoji avatars
USER_ICONS = {
    "Tim": "🦄",
    "Rareș": "🦭",
    "Rebecca": "🐿️"
}

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
        initial_df = pd.DataFrame(columns=["date", "drink_type", "volume", "abv", "units", "drinks"])
        initial_df.to_csv(f, index=False)
        # return pd.DataFrame(columns=["date", "drink_type", "volume", "abv", "units", "drinks"])
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
        else:
            trend = "→"

    daily_data.append([u, units_today, drinks_today, round(score_today, 1), trend])

daily_df = pd.DataFrame(daily_data, columns=["User", "Units", "Drinks", "Score", "Trend"])
daily_df = daily_df.sort_values(by="Score", ascending=False)

# Add emoji avatars
daily_df["User"] = daily_df["User"].apply(lambda u: f"{USER_ICONS[u]} {u}")

# Add crown to winner
daily_df.iloc[0, daily_df.columns.get_loc("User")] += " 👑"

# Convert to styled HTML
def style_leaderboard(df):
    html = df.to_html(index=False, escape=False)
    rows = html.split("<tr>")
    header = rows[1]
    body = rows[2:]

    styled_rows = []
    for i, row in enumerate(body):
        if i == 0:
            styled_rows.append(f'<tr class="gold-row">{row}')
        elif i == 1:
            styled_rows.append(f'<tr class="silver-row">{row}')
        elif i == 2:
            styled_rows.append(f'<tr class="bronze-row">{row}')
        else:
            styled_rows.append(f'<tr>{row}')

    final_html = "<table>" + "<tr>" + header + "".join(styled_rows) + "</table>"
    return final_html

st.markdown(style_leaderboard(daily_df), unsafe_allow_html=True)

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

# Add emoji avatars
weekly_df["User"] = weekly_df["User"].apply(lambda u: f"{USER_ICONS[u]} {u}")

st.table(weekly_df)

# -----------------------------
# AUDIT LINK
# -----------------------------
st.markdown("""
### Check your drinking habits
Take the official AUDIT alcohol screening test:  
https://auditscreen.org/check-your-drinking/
""")
