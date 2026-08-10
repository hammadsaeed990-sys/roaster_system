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
        # 1. Agar API key nahi hai toh email nahi bhejega
        if not SENDGRID_API_KEY:
            print("❌ ERROR: SendGrid API Key is missing from Render Environment!")
            return False

        # 2. Agar employee ka email nahi hai toh bhi fail
        if not employee_email:
            print("❌ ERROR: Employee email address is empty!")
            return False

        # 3. Email ka content build karo (Safely)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        body = f"Hello {employee_name},\n\n"
        body += f"Your work roster has been uploaded successfully.\n"
        body += f"📅 Week Starting: {week_start}\n\n"
        body += f"📋 YOUR ROSTER\n"
        body += f"{'-' * 40}\n"
        
        for day in days:
            shift = shifts.get(day, "OFF") if shifts else "OFF"
            location = locations.get(day, "") if locations else ""
            body += f"{day.capitalize()}:\n"
            body += f"Shift: {shift}\n"
            body += f"Location: {location if location else 'N/A'}\n\n"

        body += f"{'-' * 40}\n"
        body += f"Please check your roster carefully.\n\n"
        body += f"Regards,\nTask Force"

        # 4. SendGrid ke liye Email object tayyar karo
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=employee_email,
            subject=f"Your Work Roster - Week Starting {week_start}",
            plain_text_content=body
        )

        # 5. Email bhejo
        sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        # 6. Agar status code 202 (Accepted) hai toh email gayi
        if response.status_code == 202:
            print(f"✅ EMAIL SENT SUCCESSFULLY to {employee_email}")
            return True
        else:
            print(f"❌ SendGrid returned status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
