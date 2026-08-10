import os
import smtplib
from email.message import EmailMessage


def send_roster_email(
    employee_name,
    employee_email,
    week_start,
    shifts,
    locations
):
    try:
        print("========== EMAIL FUNCTION STARTED ==========")
        print(f"TO: {employee_email}")

        sender_email = os.environ.get("SENDER_EMAIL")
        app_password = os.environ.get("SENDER_APP_PASSWORD")

        print(f"SENDER_EMAIL EXISTS: {bool(sender_email)}")
        print(f"APP PASSWORD EXISTS: {bool(app_password)}")

        if not sender_email:
            print("ERROR: SENDER_EMAIL missing")
            return False

        if not app_password:
            print("ERROR: SENDER_APP_PASSWORD missing")
            return False

        message = EmailMessage()

        message["Subject"] = (
            f"Your Work Roster - Week Starting {week_start}"
        )

        message["From"] = sender_email
        message["To"] = employee_email

        body = f"""
Hello {employee_name},

Your work roster has been uploaded successfully.

Week Starting: {week_start}

YOUR ROSTER

Monday:
Shift: {shifts.get("monday", "OFF")}
Location: {locations.get("monday", "")}

Tuesday:
Shift: {shifts.get("tuesday", "OFF")}
Location: {locations.get("tuesday", "")}

Wednesday:
Shift: {shifts.get("wednesday", "OFF")}
Location: {locations.get("wednesday", "")}

Thursday:
Shift: {shifts.get("thursday", "OFF")}
Location: {locations.get("thursday", "")}

Friday:
Shift: {shifts.get("friday", "OFF")}
Location: {locations.get("friday", "")}

Saturday:
Shift: {shifts.get("saturday", "OFF")}
Location: {locations.get("saturday", "")}

Sunday:
Shift: {shifts.get("sunday", "OFF")}
Location: {locations.get("sunday", "")}

Please check your roster carefully.

Regards,
Task Force
"""

        message.set_content(body)

        print("CONNECTING TO GMAIL...")

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=20
        ) as server:

            server.ehlo()

            print("STARTING TLS...")

            server.starttls()

            server.ehlo()

            print("LOGGING INTO GMAIL...")

            server.login(
                sender_email,
                app_password
            )

            print("GMAIL LOGIN SUCCESSFUL")

            server.send_message(message)

            print("EMAIL SENT SUCCESSFULLY")

        return True

    except Exception as exc:

        print("========== EMAIL ERROR ==========")
        print(f"ERROR TYPE: {type(exc).__name__}")
        print(f"ERROR: {exc}")
        print("=================================")

        return False
