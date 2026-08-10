import os
import smtplib
from email.message import EmailMessage


SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")


def send_roster_email(
    employee_name,
    employee_email,
    week_start,
    shifts,
    locations
):

    try:

        if not SENDER_EMAIL:
            print("ERROR: SENDER_EMAIL is not configured.")
            return False

        if not SENDER_APP_PASSWORD:
            print("ERROR: SENDER_APP_PASSWORD is not configured.")
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
===========

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

        print(f"Connecting to Gmail SMTP...")
        print(f"Sending email to {employee_email}...")

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=20
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                SENDER_EMAIL,
                SENDER_APP_PASSWORD
            )

            server.send_message(message)

        print(
            f"Email sent successfully to {employee_email}"
        )

        return True

    except Exception as exc:

        print(
            f"EMAIL ERROR for {employee_email}: "
            f"{type(exc).__name__}: {exc}"
        )

        return False
