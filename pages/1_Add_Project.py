# pages/1_Add_Project.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def calculate_working_hours(start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    return len(dates) * 8

# DB connection
conn = sqlite3.connect("data_services.db", check_same_thread=False)
c = conn.cursor()

st.title("➕ Add Project")

# Load team members
team_df = pd.read_sql_query("SELECT id, name FROM team_members ORDER BY name", conn)
team_names = team_df["name"].tolist()

# Dropdown values
countries = ["Kenya", "Uganda", "Tanzania", "South Africa", "Zambia", "Nigeria", "Ghana", "Mozambique", "France", "USA", "Malawi", "Ethiopia", "Ivory Coast", "Mauritius", "Other"]
services = ["MSU", "BHT", "Innovation", "AUM", "PA", "CX", "Observer", "RCI", "IUU", "Strategy 3", "Interco", "ASI"]
activities = ["Scripting", "Analysis", "Samplying", "DBA", "Validation"]
yes_no = ["Yes", "No"]
impacts = ["On Track", "Warning", "Problem"]
priorities = ["Low", "Medium", "High", "Urgent"]
statuses = ["Not Started", "In Progress", "Completed", "Blocked", "Deferred"]

# Input form
with st.form("add_project_form"):
    project_name = st.text_input("Project Name")
    resource_name = st.selectbox("Resource", team_names)
    client_country = st.selectbox("Client Country", countries)
    service_line = st.selectbox("Service Line", services)
    available = st.selectbox("Resource Available in Kenya", yes_no)
    activity = st.selectbox("Activity", activities)
    partners_needed = st.selectbox("Partners Needed (B/T/T)", yes_no)
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    # Calculate suggested hours from dates
    suggested_hours = max(0, calculate_working_hours(start_date, end_date))
    st.info(f"Suggested Hours Based on Dates: **{suggested_hours} hrs**")

    # Manual input for hours
    hours = st.number_input("Assigned Hours (Manual Input)", min_value=0, value=suggested_hours, step=1)

    priority = st.selectbox("Priority", priorities)
    status = st.selectbox("Status", statuses)
    impact = st.selectbox("Impact", impacts)
    comments = st.text_area("Comments")

    submitted = st.form_submit_button("💾 Save Project")

    if submitted:
        resource_id = int(team_df[team_df["name"] == resource_name]["id"].values[0])

        # Insert new project
        conn.execute("""
            INSERT INTO projects (
                project_name, resource_id, client_country, service_line,
                resource_available_in_kenya, activity, partners_needed,
                start_date, end_date, hours, priority, status, impact, comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_name, resource_id, client_country, service_line,
            available, activity, partners_needed,
            start_date.isoformat(), end_date.isoformat(), hours,
            priority, status, impact, comments
        ))
        conn.commit()

        # Update assigned_hours for this resource
        conn.execute("""
            UPDATE team_members
            SET assigned_hours = (
                SELECT COALESCE(SUM(hours), 0)
                FROM projects
                WHERE resource_id = ?
            )
            WHERE id = ?
        """, (resource_id, resource_id))
        conn.commit()

        st.success("✅ Project saved and hours updated!")
