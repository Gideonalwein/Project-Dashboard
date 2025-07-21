import streamlit as st
import sqlite3
import pandas as pd
import re

st.title("👥 Manage Team Members")

conn = sqlite3.connect("data_services.db", check_same_thread=False)
cursor = conn.cursor()

# Get unique activities for role dropdown
activities = [row[0] for row in cursor.execute("SELECT DISTINCT activity FROM projects WHERE activity IS NOT NULL").fetchall()]

# -------------------------------
# ➕ Add New Member
# -------------------------------
st.subheader("➕ Add New Team Member")
with st.form("add_member"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    role = st.selectbox("Role", activities)

    if st.form_submit_button("Add Member"):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("❌ Please enter a valid email address.")
        elif not name:
            st.error("❌ Name is required.")
        else:
            # Check if email already exists
            existing = cursor.execute("SELECT id FROM team_members WHERE email = ?", (email,)).fetchone()
            if existing:
                st.error("⚠️ A team member with this email already exists.")
            else:
                cursor.execute("INSERT INTO team_members (name, email, role) VALUES (?, ?, ?)", (name, email, role))
                conn.commit()
                st.success(f"✅ {name} added successfully.")

# -------------------------------
# 📝 Team Members List
# -------------------------------
st.subheader("📝 Team Members List")
df = pd.read_sql_query("""
    SELECT tm.id, tm.name, tm.email, tm.role,
           COALESCE(SUM(p.hours), 0) AS assigned_hours
    FROM team_members tm
    LEFT JOIN projects p ON tm.id = p.resource_id
    GROUP BY tm.id, tm.name, tm.email, tm.role
""", conn)

# Total row at bottom
total_hours = df["assigned_hours"].sum()
total_row = pd.DataFrame({
    "id": [""],
    "name": ["**Total**"],
    "email": [""],
    "role": [""],
    "assigned_hours": [total_hours]
})
df_with_total = pd.concat([df, total_row], ignore_index=True)

# Editable table (exclude total row)
edited_df = st.data_editor(df_with_total.iloc[:-1], use_container_width=True, disabled=["id", "assigned_hours"], key="edit")

# Show total separately
st.markdown(f"**🔢 Total Assigned Hours: `{int(total_hours)}`**")

# -------------------------------
# 💾 Save Changes
# -------------------------------
if st.button("💾 Save Changes"):
    for i, row in edited_df.iterrows():
        cursor.execute("UPDATE team_members SET name=?, email=?, role=? WHERE id=?",
                       (row["name"], row["email"], row["role"], row["id"]))
    conn.commit()
    st.success("✅ Team member(s) updated.")

# -------------------------------
# 🗑️ Delete Member
# -------------------------------
st.subheader("🗑️ Delete Team Member")
member_ids = df["id"].tolist()
member_names = df["name"].tolist()
member_map = dict(zip(member_names, member_ids))

selected = st.selectbox("Select Member to Delete", member_names)
if st.button("Delete Member"):
    cursor.execute("UPDATE projects SET resource_id=NULL WHERE resource_id=?", (member_map[selected],))
    cursor.execute("DELETE FROM team_members WHERE id=?", (member_map[selected],))
    conn.commit()
    st.success(f"🗑️ {selected} deleted.")
