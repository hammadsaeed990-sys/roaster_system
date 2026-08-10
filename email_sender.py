import os
import smtplib
from email.message import EmailMessage


SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "").strip()
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "").replace(" ", "").strip()


def send_roster_email(
    employee_name,
    employee_email,
    week_start,
    shifts,
    locations
):
    try:
        print("==========================================")
        print("EMAIL FUNCTION STARTED")
        print(f"Sender configured: {bool(SENDER_EMAIL)}")
        print(f"Password configured: {bool(SENDER_APP_PASSWORD)}")
        print(f"Recipient: {employee_email}")
        print("==========================================")

        if not SENDER_EMAIL:
            print("EMAIL ERROR: SENDER_EMAIL is missing.")
            return False

        if not SENDER_APP_PASSWORD:
            print("EMAIL ERROR: SENDER_APP_PASSWORD is missing.")
            return False

        message = EmailMessage()

        message["Subject"] = (
            f"Your Work Roster - Week Starting {week_start}"
        )

        message["From"] = SENDER_EMAIL
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

        print("Connecting to Gmail SMTP...")

        # Gmail SMTP SSL
        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=30
        ) as server:

            print("Connected to Gmail SMTP.")

            server.login(
                SENDER_EMAIL,
                SENDER_APP_PASSWORD
            )

            print("Gmail login successful.")

            server.send_message(message)

            print(
                f"EMAIL SENT SUCCESSFULLY TO: {employee_email}"
            )

        print("==========================================")
        return True

    except smtplib.SMTPAuthenticationError as exc:
        print("==========================================")
        print("GMAIL AUTHENTICATION ERROR")
        print(repr(exc))
        print("Check Gmail App Password and SENDER_EMAIL.")
        print("==========================================")
        return False

    except smtplib.SMTPException as exc:
        print("==========================================")
        print("GMAIL SMTP ERROR")
        print(repr(exc))
        print("==========================================")
        return False

    except Exception as exc:
        print("==========================================")
        print("EMAIL ERROR")
        print(f"Type: {type(exc).__name__}")
        print(f"Error: {exc!r}")
        print("==========================================")
        return False
