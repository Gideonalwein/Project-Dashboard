import win32com.client as win32

# During development, all emails go to this test email
TEST_EMAIL = "Gideon.Okinyi@ipsos.com"  # Replace with your test email
DEVELOPMENT_MODE = True  # Set False for production use

def send_assignment_email(to_email, member_name, project_name, start_date, end_date):
    try:
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        if DEVELOPMENT_MODE:
            to_email = TEST_EMAIL

        mail.To = to_email
        mail.Subject = f"📌 Project Assignment: {project_name}"
        mail.Body = f"""
Hello {member_name},

You have been assigned to the project: {project_name}.

📅 Start Date: {start_date}
📅 End Date: {end_date}

Please log into the system to check your tasks.

Regards,
Data Services Team
        """.strip()

        mail.Send()
        print(f"✅ Email sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
