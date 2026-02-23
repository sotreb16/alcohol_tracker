import plotly.express as px

def daily_units_chart(df):
    daily = df.groupby(df["date"].dt.date)["units"].sum().reset_index()
    return px.line(daily, x="date", y="units", title="Daily Units")

def weekly_units_chart(df):
    df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly = df.groupby("week")["units"].sum().reset_index()
    return px.bar(weekly, x="week", y="units", title="Weekly Units")
