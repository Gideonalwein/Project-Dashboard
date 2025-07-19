import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from io import BytesIO

# -----------------------------
# Connect to database
# -----------------------------
conn = sqlite3.connect("data_services.db", check_same_thread=False)

st.title("📊 Workload Summary by Team Member")

# -----------------------------
# Load team members and projects
# -----------------------------
team_df = pd.read_sql_query("SELECT id as team_member_id, name, email, role FROM team_members", conn)
projects_df = pd.read_sql_query("SELECT * FROM projects", conn)

# -----------------------------
# Calculate assigned hours
# -----------------------------
if team_df.empty:
    st.warning("⚠️ No team member data found.")
    st.stop()

if projects_df.empty:
    st.warning("⚠️ No project data found.")
    st.stop()

merged_df = pd.merge(
    team_df,
    projects_df,
    how="left",
    left_on="team_member_id",
    right_on="resource_id"
)

summary_df = merged_df.groupby(["team_member_id", "name", "email", "role"], as_index=False)["hours"].sum()
summary_df.rename(columns={"hours": "assigned_hours"}, inplace=True)
summary_df["assigned_hours"] = summary_df["assigned_hours"].fillna(0).astype(int)

# -----------------------------
# 💡 Threshold for underutilized members
# -----------------------------
threshold = st.slider("💡 Set Hour Threshold (below this = underutilized)", min_value=0, max_value=100, value=8)
underutilized = summary_df[summary_df["assigned_hours"] < threshold]

if not underutilized.empty:
    st.warning(f"⚠️ Underutilized Members (< {threshold} hrs):")
    st.dataframe(underutilized[["name", "role", "assigned_hours"]], use_container_width=True)
else:
    st.success("✅ No underutilized members below the threshold.")

# -----------------------------
# 🔍 Filter by Role
# -----------------------------
with st.expander("🔍 Filter by Role"):
    available_roles = summary_df["role"].dropna().unique().tolist()
    selected_roles = st.multiselect("Select Roles to View", available_roles, default=available_roles)
    summary_df = summary_df[summary_df["role"].isin(selected_roles)]

# -----------------------------
# 📋 Display Table
# -----------------------------
st.subheader("📋 Workload Table")
st.dataframe(summary_df, use_container_width=True)

# -----------------------------
# 💾 Download to Excel
# -----------------------------
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    summary_df.to_excel(writer, index=False, sheet_name="Workload Summary")

st.download_button(
    label="📥 Download Summary as Excel",
    data=excel_buffer.getvalue(),
    file_name="workload_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# -----------------------------
# 📊 Workload Bar Chart
# -----------------------------
st.subheader("📊 Assigned Hours per Team Member")

fig = px.bar(
    summary_df,
    x="name",
    y="assigned_hours",
    color="role",
    title="Assigned Hours by Team Member",
    labels={"assigned_hours": "Hours"},
    height=450
)
st.plotly_chart(fig, use_container_width=True)
