import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

st.set_page_config(page_title="Alcohol Tracker Game", layout="centered")

# -----------------------------
# GOOGLE SHEETS CONNECTION
# -----------------------------
SHEET_NAME = "Alcohol Tracker Data"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(creds)


def get_worksheet(user):
    """Return worksheet, create if missing."""
    try:
        return client.open(SHEET_NAME).worksheet(user)
    except gspread.WorksheetNotFound:
        sh = client.open(SHEET_NAME)
        ws = sh.add_worksheet(title=user, rows=1000, cols=10)
        ws.append_row(["date", "drink_type", "volume", "abv", "units", "drinks", "note"])
        return ws

def load_user_df(user):
    ws = get_worksheet(user)
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=["date", "drink_type", "volume", "abv", "units", "drinks", "note"])
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def append_row(user, row_dict):
    ws = get_worksheet(user)
    ws.append_row(list(row_dict.values()))

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
body { background: linear-gradient(135deg, #f2f2f2 0%, #e6e6e6 100%) !important; }
.block-container { padding-top: 2rem; }
h1, h2, h3, h4 { color: #FF8C42 !important; }
.stButton>button {
    background-color: #FF8C42 !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton>button:hover { background-color: #ffa766 !important; }
table { border-collapse: collapse; width: 100%; border-radius: 12px; overflow: hidden; }
thead tr th { background-color: #FF8C42 !important; color: white !important; padding: 10px; }
tbody tr:nth-child(even) { background-color: #fafafa; }
tbody tr:nth-child(odd) { background-color: #ffffff; }
tbody tr:hover { background-color: #ffe8d6 !important; }
tr.gold-row { background-color: #FFD700 !important; }
tr.silver-row { background-color: #C0C0C0 !important; }
tr.bronze-row { background-color: #CD7F32 !important; }
td { font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# USERS
# -----------------------------
USERS = ["Tim", "Rares", "Bogdan"]

USER_ICONS = {
    "Tim": "🦄",
    "Rares": "🦭",
    "Bogdan": "🐿️"
}

user = st.selectbox("Who is using the app?", USERS)

# -----------------------------
# SCORING FUNCTIONS
# -----------------------------
def calculate_units(volume, abv):
    return volume * (abv / 100) * 0.789

def daily_score(units_today):
    score = 100 - (units_today / 2) * 50
    return max(0, round(score, 1))

def weekly_score(units_week):
    score = 100 - (units_week / 14) * 50
    return max(0, round(score, 1))

# -----------------------------
# LOGGING DRINKS
# -----------------------------
st.header("Log your drinks")

drink_type = st.text_input("Drink type (Beer, Wine, etc.)")
volume = st.number_input("Volume (ml)", min_value=0.0)
abv = st.number_input("ABV (%)", min_value=0.0)
note = st.text_input("Note for this drink (optional)")

if st.button("Add drink"):
    if drink_type and volume > 0 and abv > 0:
        units = calculate_units(volume, abv)
        append_row(user, {
            "date": str(datetime.now().date()),
            "drink_type": drink_type,
            "volume": volume,
            "abv": abv,
            "units": units,
            "drinks": 1,
            "note": note
        })
        st.success("Drink added!")
    else:
        st.warning("Please enter drink type, volume and ABV.")

if st.button("0 alcohol today"):
    append_row(user, {
        "date": str(datetime.now().date()),
        "drink_type": "None",
        "volume": 0,
        "abv": 0,
        "units": 0,
        "drinks": 0,
        "note": ""
    })
    st.success("Logged a sober day!")

# -----------------------------
# DAILY LEADERBOARD
# -----------------------------
st.header("Daily Leaderboard")

today = datetime.now().date()
daily_rows = []

for u in USERS:
    df = load_user_df(u)
    today_df = df[df["date"] == today] if not df.empty else pd.DataFrame()
    units_today = today_df["units"].sum() if not today_df.empty else 0
    drinks_today = today_df["drinks"].sum() if not today_df.empty else 0
    score_today = daily_score(units_today)
    daily_rows.append([u, round(units_today, 1), drinks_today, score_today])

daily_df = pd.DataFrame(daily_rows, columns=["User", "Units", "Drinks", "Score"])
daily_df = daily_df.sort_values(by="Score", ascending=False)
daily_df["User"] = daily_df["User"].apply(lambda u: f"{USER_ICONS[u]} {u}")
daily_df.iloc[0, daily_df.columns.get_loc("User")] += " 👑"

def style_table(df):
    html = df.to_html(index=False, escape=False)
    rows = html.split("<tr>")
    header = rows[1]
    body = rows[2:]
    styled = []
    for i, row in enumerate(body):
        if i == 0: styled.append(f'<tr class="gold-row">{row}')
        elif i == 1: styled.append(f'<tr class="silver-row">{row}')
        elif i == 2: styled.append(f'<tr class="bronze-row">{row}')
        else: styled.append(f'<tr>{row}')
    return "<table><tr>" + header + "".join(styled) + "</table>"

st.markdown(style_table(daily_df), unsafe_allow_html=True)

# -----------------------------
# WEEKLY LEADERBOARD
# -----------------------------
st.header("Weekly Leaderboard")

week_ago = today - timedelta(days=7)
weekly_rows = []

for u in USERS:
    df = load_user_df(u)
    df = df[df["date"] >= week_ago] if not df.empty else df
    units_week = df["units"].sum() if not df.empty else 0
    drinks_week = df["drinks"].sum() if not df.empty else 0
    score_w = weekly_score(units_week)
    weekly_rows.append([u, round(units_week, 1), drinks_week, score_w])

weekly_df = pd.DataFrame(weekly_rows, columns=["User", "Units (7d)", "Drinks (7d)", "Score (7d)"])
weekly_df = weekly_df.sort_values(by="Score (7d)", ascending=False)
weekly_df["User"] = weekly_df["User"].apply(lambda u: f"{USER_ICONS[u]} {u}")

st.table(weekly_df)

# -----------------------------
# WEEKLY SUMMARY (BUTTON)
# -----------------------------
st.header("Weekly Summary")

if st.button("Show Weekly Summary"):
    df = load_user_df(user)
    df = df[df["date"] >= week_ago]

    if df.empty:
        st.info("No data for the last 7 days.")
    else:
        units_week = df["units"].sum()
        drinks_week = df["drinks"].sum()
        sober_days = (df.groupby("date")["units"].sum() == 0).sum()
        avg_units = units_week / 7
        score_w = weekly_score(units_week)

        daily_units = df.groupby("date")["units"].sum().reset_index()
        best_day = daily_units.loc[daily_units["units"].idxmin()]
        worst_day = daily_units.loc[daily_units["units"].idxmax()]

        st.subheader(f"Summary for {user}")
        st.metric("Total units (7d)", round(units_week, 1))
        st.metric("Total drinks (7d)", int(drinks_week))
        st.metric("Weekly score", score_w)
        st.metric("Sober days", int(sober_days))
        st.metric("Average units/day", round(avg_units, 2))

        st.subheader("Best & Worst Days")
        st.write(f"Best day: {best_day['date']} — {round(best_day['units'],1)} units")
        st.write(f"Worst day: {worst_day['date']} — {round(worst_day['units'],1)} units")

        st.subheader("Units per day")
        st.line_chart(daily_units.set_index("date"))

        st.subheader("Notes from this week")
        notes = df[df["note"].astype(str).str.strip() != ""]
        if notes.empty:
            st.write("No notes this week.")
        else:
            for _, row in notes.iterrows():
                st.write(f"- **{row['date']}** — {row['drink_type']}: {row['note']}")

# -----------------------------
# AUDIT LINK
# -----------------------------
st.markdown("""
### Check your drinking habits
Take the official AUDIT alcohol screening test:  
https://auditscreen.org/check-your-drinking/
""")
