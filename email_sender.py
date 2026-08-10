import os
import sendgrid
from sendgrid.helpers.mail import Mail

# Render ke Environment variables se uthayega
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hammadsaeed990@gmail.com")

def send_roster_email(employee_name, employee_email, week_start, shifts, locations):
    """
    Send roster email using SendGrid (Real emails ke liye)
    """
    try:
        # Agar API key nahi hai toh email nahi bhejega
        if not SENDGRID_API_KEY:
            print("❌ ERROR: SendGrid API Key is missing from Render Environment!")
            return False

        # Email ka content build karo
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        body = f"""
Hello {employee_name},

Your work roster has been uploaded successfully.

📅 Week Starting: {week_start}

📋 YOUR ROSTER
{'-' * 40}
"""
        for day in days:
            shift = shifts.get(day, "OFF") if shifts else "OFF"
            location = locations.get(day, "") if locations else ""
            body += f"""
{day.capitalize()}:
Shift: {shift}
Location: {location if location else 'N/A'}
"""

        body += f"""
{'-' * 40}
Please check your roster carefully.

Regards,
Task Force
"""

        # SendGrid ke liye Email object tayyar karo
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=employee_email,
            subject=f"Your Work Roster - Week Starting {week_start}",
            plain_text_content=body
        )

        # Email bhejo
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # Agar status code 202 (Accepted) hai toh email gayi
        if response.status_code == 202:
            print(f"✅ EMAIL SENT SUCCESSFULLY to {employee_email}")
            return True
        else:
            print(f"❌ SendGrid returned status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
