import streamlit as st
import os

st.title("💾 Export SQLite Database")

db_path = "data_services.db"

if os.path.exists(db_path):
    with open(db_path, "rb") as file:
        st.download_button(
            label="📥 Download Full Database Backup",
            data=file,
            file_name="data_services_backup.db",
            mime="application/octet-stream"
        )
else:
    st.error("❌ Database file not found.")
