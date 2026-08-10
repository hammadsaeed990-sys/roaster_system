import os
import sendgrid
from sendgrid.helpers.mail import Mail

# Render ke Environment variables se uthayega
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "hammadsaeed990@gmail.com").strip()

def send_roster_email(employee_name, employee_email, week_start, shifts, locations):
    """
    Send roster email using SendGrid
    """
    try:
        print("=" * 60)
        print("📧 SENDGRID EMAIL FUNCTION STARTED")
        print(f"🔑 API KEY EXISTS: {'✅ YES' if SENDGRID_API_KEY else '❌ NO'}")
        print(f"📤 SENDER EMAIL: {SENDER_EMAIL}")
        print(f"📥 RECIPIENT: {employee_email}")
        print("=" * 60)

        # --- CHECKS ---
        if not SENDGRID_API_KEY:
            print("❌ ERROR: SENDGRID_API_KEY is missing in Render Environment!")
            return False

        if not SENDER_EMAIL:
            print("❌ ERROR: SENDER_EMAIL is missing!")
            return False

        if not employee_email:
            print("❌ ERROR: Employee email is empty!")
            return False

        # --- BUILD EMAIL BODY ---
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        body = f"""Hello {employee_name},

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

        # --- SEND EMAIL ---
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=employee_email,
            subject=f"Your Work Roster - Week Starting {week_start}",
            plain_text_content=body
        )

        print("📤 Sending request to SendGrid API...")
        
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # --- RESULT ---
        print("=" * 60)
        print(f"📊 STATUS CODE: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ EMAIL SENT SUCCESSFULLY to {employee_email}")
            print("=" * 60)
            return True
        else:
            print(f"❌ SendGrid returned status: {response.status_code}")
            print(f"📄 Response Body: {response.body}")
            print("=" * 60)
            return False

    except Exception as exc:
        print("=" * 60)
        print("❌ UNEXPECTED ERROR IN SENDGRID FUNCTION")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error Details: {exc}")
        print("=" * 60)
        return False
