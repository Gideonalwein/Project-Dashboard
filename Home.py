import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Project Dashboard", layout="wide")
st.title("📊 Data Services Project Dashboard")

# Connect DB
conn = sqlite3.connect("data_services.db", check_same_thread=False)

# Load project data
query = """
SELECT 
    p.id, p.project_name, tm.name AS resource, p.client_country,
    p.service_line, p.resource_available_in_kenya, p.activity,
    p.partners_needed, p.start_date, p.end_date, p.hours,
    p.priority, p.status, p.impact, p.comments
FROM projects p
LEFT JOIN team_members tm ON p.resource_id = tm.id
"""
df = pd.read_sql_query(query, conn, parse_dates=["start_date", "end_date"])

# Format impact with emojis
impact_badges = {
    "On Track": "🟢 On Track",
    "Warning": "🟡 Warning",
    "Problem": "🔴 Problem"
}
df["impact_display"] = df["impact"].map(impact_badges)

# Ensure datetime conversion
df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

# 🔍 Filters Section
st.markdown("### 🔎 Filter Projects")

col1, col2, col3 = st.columns(3)

# Date Range Filter
filter_start = col1.date_input("Start Date", value=None)
filter_end = col2.date_input("End Date", value=None)

# Resource Filter
resource_options = ["All"] + sorted(df["resource"].dropna().unique().tolist())
selected_resource = col3.selectbox("Filter by Resource", resource_options)

# Activity Filter
activity_options = ["All"] + sorted(df["activity"].dropna().unique().tolist())
selected_activity = st.selectbox("Filter by Activity", activity_options)

# Country Filter
country_options = ["All"] + sorted(df["client_country"].dropna().unique().tolist())
selected_country = st.selectbox("Filter by Country", country_options)

# Apply filters
if filter_start and filter_end:
    df = df[
        (df["start_date"].notnull()) & (df["end_date"].notnull()) &
        (df["start_date"] >= pd.to_datetime(filter_start)) &
        (df["end_date"] <= pd.to_datetime(filter_end))
    ]

if selected_resource != "All":
    df = df[df["resource"] == selected_resource]

if selected_activity != "All":
    df = df[df["activity"] == selected_activity]

if selected_country != "All":
    df = df[df["client_country"] == selected_country]

st.info(f"🔍 {len(df)} projects match your filters.")

# 📌 Summary
st.markdown("### 📌 Project Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Projects", len(df))
col2.metric("Total Planned Hours", int(df["hours"].sum()))
col3.metric("Unique Resources", df["resource"].nunique())

# ✅ Show count of projects completed in the last 7 days
seven_days_ago = datetime.today() - timedelta(days=7)
recent_completed = df[
    (df["status"] == "Completed") &
    (df["end_date"] >= seven_days_ago)
]
st.metric("✅ Completed in Last 7 Days", len(recent_completed))

# 📋 Table of Projects
st.markdown("### 📋 Project Table")
display_df = df[[ 
    "project_name", "resource", "client_country", "service_line",
    "activity", "start_date", "end_date", "hours", 
    "priority", "status", "impact_display", "comments"
]].rename(columns={"project_name": "Project", "impact_display": "Impact"})

st.dataframe(display_df, use_container_width=True, hide_index=True)

# 📊 Charts
st.markdown("### 📊 Project Insights")

# Chart Row 1
c1, c2 = st.columns(2)

impact_grouped = df.groupby("impact").agg(
    count=("id", "count"),
    avg_hours=("hours", "mean")
).reset_index()

with c1:
    fig1 = px.pie(
        impact_grouped,
        names="impact",
        values="count",
        title="Impact Distribution",
        color="impact",
        hole=0.4,
        color_discrete_map={"On Track": "green", "Warning": "orange", "Problem": "red"},
        hover_data=["count", "avg_hours"]
    )
    fig1.update_traces(textinfo='label+percent+value')
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    fig2 = px.histogram(
        df,
        x="priority",
        color="priority",
        title="Project Priorities",
        color_discrete_sequence=px.colors.qualitative.Set1,
        hover_data=["project_name", "status", "hours", "activity"]
    )
    st.plotly_chart(fig2, use_container_width=True)

# Chart Row 2: Country
country_grouped = df.groupby("client_country").agg(
    count=("id", "count"),
    total_hours=("hours", "sum")
).reset_index()

fig3 = px.pie(
    country_grouped,
    names="client_country",
    values="count",
    title="Projects by Country (Markets)",
    hole=0.35,
    hover_data=["count", "total_hours"]
)
fig3.update_traces(textinfo='label+percent+value')
st.plotly_chart(fig3, use_container_width=True)
