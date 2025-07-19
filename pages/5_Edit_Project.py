import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- Helper ---
def calculate_working_hours(start_date, end_date):
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days only
    return len(dates) * 8

# --- DB Connection ---
conn = sqlite3.connect("data_services.db", check_same_thread=False)
st.title("✏️ Edit or Delete Projects")

# --- Load Data ---
team_df = pd.read_sql_query("SELECT id, name FROM team_members ORDER BY name", conn)
project_df = pd.read_sql_query("SELECT * FROM projects ORDER BY project_name", conn)

# --- Dropdown Options ---
countries = ["Kenya", "Uganda", "Tanzania", "South Africa", "Zambia", "Nigeria", "Ghana", "Mozambique", "France", "USA", "Malawi", "Ethiopia", "Ivory Coast", "Mauritius", "Other"]
services = ["MSU", "BHT", "Innovation", "AUM", "PA", "CX", "Observer", "RCI", "IUU", "Strategy 3", "Interco", "ASI"]
activities = ["Scripting", "Analysis", "Samplying", "DBA", "Validation"]
yes_no = ["Yes", "No"]
impacts = ["On Track", "Warning", "Problem"]
priorities = ["Low", "Medium", "High", "Urgent"]
statuses = ["Not Started", "In Progress", "Completed", "Blocked", "Deferred"]

# --- Project Selector with Placeholder ---
project_names = project_df["project_name"].tolist()
project_selection = st.selectbox("📌 Select Project", ["-- Select a project --"] + project_names)

if project_selection and project_selection != "-- Select a project --":
    data = project_df[project_df["project_name"] == project_selection].iloc[0]

    try:
        project_id = int(data["id"])  # Ensure ID is int and usable in SQL
    except Exception as e:
        st.error(f"❌ Error resolving project ID: {e}")
        st.stop()

    with st.form("edit_project_form"):
        # Resolve Resource index
        default_resource_id = int(data["resource_id"]) if pd.notnull(data["resource_id"]) else team_df.iloc[0]["id"]
        default_index = team_df[team_df["id"] == default_resource_id].index.tolist()
        default_index = default_index[0] if default_index else 0

        # Editable Inputs
        project_name = st.text_input("Project Name", value=data["project_name"])
        resource = st.selectbox("Resource", team_df["name"].tolist(), index=default_index)
        client_country = st.selectbox("Client Country", countries, index=countries.index(data["client_country"]) if data["client_country"] in countries else 0)
        service_line = st.selectbox("Service Line", services, index=services.index(data["service_line"]) if data["service_line"] in services else 0)
        available = st.selectbox("Resource Available in Kenya", yes_no, index=yes_no.index(data["resource_available_in_kenya"]) if data["resource_available_in_kenya"] in yes_no else 0)
        activity = st.selectbox("Activity", activities, index=activities.index(data["activity"]) if data["activity"] in activities else 0)
        partners_needed = st.selectbox("Partners Needed (B/T/T)", yes_no, index=yes_no.index(data["partners_needed"]) if data["partners_needed"] in yes_no else 0)
        start_date = st.date_input("Start Date", value=pd.to_datetime(data["start_date"]))
        end_date = st.date_input("End Date", value=pd.to_datetime(data["end_date"]))

        calculated_hours = calculate_working_hours(start_date, end_date)
        st.info(f"🧮 Auto-calculated working hours: {calculated_hours}")

        default_hours = int(data["hours"]) if int(data["hours"]) > 0 else 1
        hours = st.number_input("Assigned Hours (Manual Input)", min_value=1, value=default_hours, step=1)

        priority = st.selectbox("Priority", priorities, index=priorities.index(data["priority"]) if data["priority"] in priorities else 0)
        status = st.selectbox("Status", statuses, index=statuses.index(data["status"]) if data["status"] in statuses else 0)
        impact = st.selectbox("Impact", impacts, index=impacts.index(data["impact"]) if data["impact"] in impacts else 0)
        comments = st.text_area("Comments", value=data["comments"] or "")

        submitted = st.form_submit_button("💾 Update Project")

    # --- Update Logic ---
    if submitted:
        new_resource_id = int(team_df[team_df["name"] == resource]["id"].values[0])

        cursor = conn.execute("""
            UPDATE projects SET
                project_name = ?, resource_id = ?, client_country = ?, service_line = ?,
                resource_available_in_kenya = ?, activity = ?, partners_needed = ?,
                start_date = ?, end_date = ?, hours = ?, priority = ?, status = ?, impact = ?, comments = ?
            WHERE id = ?
        """, (
            project_name, new_resource_id, client_country, service_line,
            available, activity, partners_needed,
            start_date.isoformat(), end_date.isoformat(), hours,
            priority, status, impact, comments, project_id
        ))
        conn.commit()
        st.success(f"✅ Project updated. Rows affected: {cursor.rowcount}")

        # Recalculate team member hours
        conn.execute("""
            UPDATE team_members
            SET assigned_hours = (
                SELECT COALESCE(SUM(p.hours), 0)
                FROM projects p
                WHERE p.resource_id = team_members.id
            )
        """)
        conn.commit()
        st.rerun()

    # --- Delete Section ---
    st.divider()
    with st.expander("🗑️ Delete This Project", expanded=False):
        st.markdown("⚠️ This action is irreversible. Confirm before proceeding.")
        col1, col2 = st.columns([1, 3])
        with col1:
            confirm_delete = st.checkbox("Confirm Delete")
        with col2:
            if st.button("❌ Delete Project"):
                if confirm_delete:
                    cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                    conn.commit()
                    st.success(f"🗑️ Project deleted. Rows affected: {cursor.rowcount}")
                    st.rerun()
                else:
                    st.warning("☝️ Please confirm deletion.")
