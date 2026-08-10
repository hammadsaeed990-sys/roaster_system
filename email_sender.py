import os
import sendgrid
from sendgrid.helpers.mail import Mail


SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get(
    "SENDER_EMAIL",
    "hammadsaeed990@gmail.com"
).strip()


def send_roster_email(
    employee_name,
    employee_email,
    week_start,
    shifts,
    locations
):
    try:
        print("==========================================")
        print("SENDGRID EMAIL FUNCTION STARTED")
        print(f"API KEY EXISTS: {bool(SENDGRID_API_KEY)}")
        print(f"SENDER EMAIL: {SENDER_EMAIL}")
        print(f"RECIPIENT: {employee_email}")
        print("==========================================")

        if not SENDGRID_API_KEY:
            print("ERROR: SENDGRID_API_KEY is missing.")
            return False

        if not SENDER_EMAIL:
            print("ERROR: SENDER_EMAIL is missing.")
            return False

        if not employee_email:
            print("ERROR: Employee email is missing.")
            return False

        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday"
        ]

        body = f"""Hello {employee_name},

Your work roster has been uploaded successfully.

Week Starting: {week_start}

YOUR ROSTER
----------------------------------------

"""

        for day in days:
            shift = (
                shifts.get(day, "OFF")
                if shifts
                else "OFF"
            )

            location = (
                locations.get(day, "")
                if locations
                else ""
            )

            body += (
                f"{day.capitalize()}:\n"
                f"Shift: {shift}\n"
                f"Location: {location or 'N/A'}\n\n"
            )

        body += """----------------------------------------

Please check your roster carefully.

Regards,
Task Force
"""

        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=employee_email,
            subject=(
                f"Your Work Roster - "
                f"Week Starting {week_start}"
            ),
            plain_text_content=body
        )

        print("Creating SendGrid client...")

        sg = sendgrid.SendGridAPIClient(
            SENDGRID_API_KEY
        )

        print("Sending request to SendGrid...")

        response = sg.send(message)

        print("==========================================")
        print(
            f"SENDGRID STATUS CODE: "
            f"{response.status_code}"
        )
        print(
            f"SENDGRID RESPONSE BODY: "
            f"{response.body}"
        )
        print(
            f"SENDGRID RESPONSE HEADERS: "
            f"{response.headers}"
        )
        print("==========================================")

        if response.status_code in [200, 201, 202]:
            print(
                f"EMAIL ACCEPTED BY SENDGRID: "
                f"{employee_email}"
            )
            return True

        print(
            f"EMAIL NOT ACCEPTED. "
            f"STATUS: {response.status_code}"
        )

        return False

    except Exception as exc:
        print("==========================================")
        print("SENDGRID EMAIL ERROR")
        print(f"ERROR TYPE: {type(exc).__name__}")
        print(f"ERROR: {repr(exc)}")
        print("==========================================")

        return False
