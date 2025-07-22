# pages/1_Add_Project.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Function to calculate business-day hours
def calculate_working_hours(start_date, end_date):
    if start_date and end_date and start_date <= end_date:
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days only
        return len(dates) * 8  # 8 hours per business day
    return 0

# DB connection
conn = sqlite3.connect("data_services.db", check_same_thread=False)
c = conn.cursor()

st.set_page_config(layout="wide")
st.title("➕ Add Project")

# Load team members
team_df = pd.read_sql_query("SELECT id, name FROM team_members ORDER BY name", conn)
team_names = ["-- Select Resource --"] + team_df["name"].tolist()

# Dropdown values
countries = ["-- Select Country --", "Kenya", "Uganda", "Tanzania", "South Africa", "Zambia", "Nigeria", "Ghana", "Mozambique", "France", "USA", "Malawi", "Ethiopia", "Ivory Coast", "Mauritius", "Other"]
services = ["-- Select Service Line --", "MSU", "BHT", "Innovation", "AUM", "PA", "CX", "Observer", "RCI", "IUU", "Strategy 3", "Interco", "ASI"]
activities = ["-- Select Activity --", "Scripting", "Analysis", "Samplying", "DBA", "Validation","PM","Script QC"]
yes_no = ["-- Select Option --", "Yes", "No"]
impacts = ["-- Select Impact --", "On Track", "Warning", "Problem"]
priorities = ["-- Select Priority --", "Low", "Medium", "High", "Urgent"]
statuses = ["-- Select Status --", "Not Started", "In Progress", "Completed", "Blocked", "Deferred"]

# Input form
with st.form("add_project_form"):
    project_name = st.text_input("Project Name")

    resource_name = st.selectbox("Resource", team_names)
    client_country = st.selectbox("Client Country", countries)
    service_line = st.selectbox("Service Line", services)
    available = st.selectbox("Resource Available in Kenya", yes_no)
    activity = st.selectbox("Activity", activities)
    partners_needed = st.selectbox("Partners Needed (B/T/T)", yes_no)

    start_date = st.date_input("Start Date", value=None)
    end_date = st.date_input("End Date", value=None)

    auto_calc = st.checkbox("⏱️ Auto-calculate hours based on Start and End Dates")

    suggested_hours = calculate_working_hours(start_date, end_date) if auto_calc else 0
    if auto_calc:
        st.info(f"🧮 Auto-calculated working hours: **{suggested_hours} hrs**")

    # Hours input (manual or calculated)
    hours = st.number_input(
        "Assigned Hours (Manual Input)",
        min_value=1,
        value=suggested_hours if suggested_hours > 0 else 1,
        step=1
    )

    priority = st.selectbox("Priority", priorities)
    status = st.selectbox("Status", statuses)
    impact = st.selectbox("Impact", impacts)
    comments = st.text_area("Comments")

    submitted = st.form_submit_button("💾 Save Project")

    # Validation
    if submitted:
        if not project_name.strip():
            st.error("Project Name is required.")
        elif resource_name == "-- Select Resource --":
            st.error("Please select a resource.")
        elif client_country == "-- Select Country --":
            st.error("Please select a client country.")
        elif service_line == "-- Select Service Line --":
            st.error("Please select a service line.")
        elif available == "-- Select Option --":
            st.error("Please select if the resource is available in Kenya.")
        elif activity == "-- Select Activity --":
            st.error("Please select an activity.")
        elif partners_needed == "-- Select Option --":
            st.error("Please select if partners are needed.")
        elif not start_date or not end_date:
            st.error("Start and End Dates are required.")
        elif priority == "-- Select Priority --":
            st.error("Please select a priority.")
        elif status == "-- Select Status --":
            st.error("Please select a status.")
        elif impact == "-- Select Impact --":
            st.error("Please select an impact.")
        else:
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
