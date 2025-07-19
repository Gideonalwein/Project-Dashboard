import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# --- Setup
st.set_page_config(layout="wide")
st.title("🏖️ Leave Management")

conn = sqlite3.connect("data_services.db", check_same_thread=False)
cursor = conn.cursor()

# --- Load data
leave_df = pd.read_sql_query("""
    SELECT tm.id, tm.name, tm.email, tm.role,
           lb.previous_year_balance,
           lb.current_year_allocated,
           lb.current_year_taken
    FROM team_members tm
    LEFT JOIN leave_balances lb ON tm.id = lb.team_member_id
    ORDER BY tm.name
""", conn)

if leave_df.empty:
    st.warning("No leave data found.")
    st.stop()

# --- Calculate balances and percentages
leave_df["current_year_balance"] = leave_df["current_year_allocated"] - leave_df["current_year_taken"]
leave_df["pct_taken"] = round((leave_df["current_year_taken"] / leave_df["current_year_allocated"]) * 100).astype(int)
leave_df["pct_balance"] = 100 - leave_df["pct_taken"]

# Add % sign for display
leave_df["pct_taken"] = leave_df["pct_taken"].astype(str) + "%"
leave_df["pct_balance"] = leave_df["pct_balance"].astype(str) + "%"

# --- Display leave table
st.subheader("📋 Team Leave Overview")
st.dataframe(leave_df, use_container_width=True)

# --- Editable Section
st.subheader("📝 Edit Leave Balances")

editable_df = st.data_editor(
    leave_df[["id", "name", "previous_year_balance", "current_year_allocated", "current_year_taken"]],
    use_container_width=True,
    num_rows="dynamic",
    disabled=["id", "name"],
    key="leave_editor"
)

if st.button("💾 Save Updates"):
    for _, row in editable_df.iterrows():
        cursor.execute("""
            INSERT INTO leave_balances (team_member_id, previous_year_balance, current_year_allocated, current_year_taken)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(team_member_id) DO UPDATE SET
                previous_year_balance = excluded.previous_year_balance,
                current_year_allocated = excluded.current_year_allocated,
                current_year_taken = excluded.current_year_taken
        """, (row["id"], row["previous_year_balance"], row["current_year_allocated"], row["current_year_taken"]))
    conn.commit()
    st.success("✅ Leave balances updated successfully.")
    st.rerun()

# --- Bar Chart
st.subheader("📊 Leave Used Per Team Member")
bar_data = leave_df.copy()
bar_data["current_year_taken"] = bar_data["current_year_taken"].astype(int)

fig = px.bar(
    bar_data,
    x="name",
    y="current_year_taken",
    color="role",
    title="Days of Leave Taken",
    labels={"current_year_taken": "Days Taken"},
    height=450
)
st.plotly_chart(fig, use_container_width=True)
