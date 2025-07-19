import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.title("📤 Import Projects from Excel")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("📄 Preview Uploaded Data")
    st.dataframe(df)

    if st.button("Import to Database"):
        conn = sqlite3.connect("data_services.db")
        cursor = conn.cursor()

        # Map team member names to IDs
        team_map = {name: id for id, name in cursor.execute("SELECT id, name FROM team_members")}

        required_cols = [
            "Project Name", "Resource", "Client Country", "Service Line",
            "Resource available in Kenya", "Activity",
            "Bulgaria/Tunisia/Thailand Partners needed (Y/N)",
            "Start Date", "End Date", "Hours",
            "Priority", "Status", "Impact"
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        else:
            inserted, skipped = 0, 0
            for _, row in df.iterrows():
                try:
                    if pd.isna(row["Project Name"]) or pd.isna(row["Start Date"]) or pd.isna(row["End Date"]):
                        skipped += 1
                        continue

                    start_date = pd.to_datetime(row["Start Date"]).date()
                    end_date = pd.to_datetime(row["End Date"]).date()

                    # Calculate hours if missing
                    if pd.notna(row.get("Hours")) and row["Hours"] > 0:
                        hours = int(row["Hours"])
                    else:
                        weekdays = pd.date_range(start=start_date, end=end_date, freq='B')
                        hours = len(weekdays) * 8

                    resource_id = team_map.get(row.get("Resource", "Not assigned"), None)

                    cursor.execute("""
                        INSERT INTO projects (
                            project_name, resource_id, client_country, service_line,
                            resource_available_in_kenya, activity, partners_needed,
                            start_date, end_date, hours,
                            priority, status, impact, comments
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row["Project Name"],
                        resource_id,
                        row.get("Client Country", ""),
                        row.get("Service Line", ""),
                        row.get("Resource available in Kenya", "No"),
                        row.get("Activity", ""),
                        row.get("Bulgaria/Tunisia/Thailand Partners needed (Y/N)", "No"),
                        start_date,
                        end_date,
                        hours,
                        row.get("Priority", "Medium"),
                        row.get("Status", "Not Started"),
                        row.get("Impact", "On Track"),
                        row.get("Comments", ""),
                    ))
                    inserted += 1
                except Exception as e:
                    skipped += 1
                    st.error(f"Error on row: {row.get('Project Name', 'Unnamed')} - {e}")

            conn.commit()
            conn.close()
            st.success(f"✅ Imported: {inserted} rows | ❌ Skipped: {skipped} invalid rows")
else:
    st.info("📎 Please upload an Excel file to enable import.")
