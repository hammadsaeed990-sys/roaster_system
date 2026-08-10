import smtplib
from email.message import EmailMessage


# ============================================================
# GMAIL SETTINGS
# ============================================================

SENDER_EMAIL = "hammadsaeed990@gmail.com"

# Apna existing Gmail App Password yahan rakho
SENDER_APP_PASSWORD = "glgs cjrp uxwi glhp"


# ============================================================
# SEND ROSTER EMAIL
# ============================================================

def send_roster_email(
    employee_name,
    employee_email,
    week_start,
    shifts,
    locations
):

    try:

        message = EmailMessage()

        message["Subject"] = (
            f"Your Work Roster - Week Starting {week_start}"
        )

        message["From"] = SENDER_EMAIL
        message["To"] = employee_email


        # ====================================================
        # EMAIL BODY
        # ====================================================

        body = f"""
Hello {employee_name},

Your work roster has been uploaded successfully.

Week Starting: {week_start}

YOUR ROSTER
==================================================

Monday:
Shift: {shifts["monday"]}
Location: {locations["monday"]}

Tuesday:
Shift: {shifts["tuesday"]}
Location: {locations["tuesday"]}

Wednesday:
Shift: {shifts["wednesday"]}
Location: {locations["wednesday"]}

Thursday:
Shift: {shifts["thursday"]}
Location: {locations["thursday"]}

Friday:
Shift: {shifts["friday"]}
Location: {locations["friday"]}

Saturday:
Shift: {shifts["saturday"]}
Location: {locations["saturday"]}

Sunday:
Shift: {shifts["sunday"]}
Location: {locations["sunday"]}


Please check your roster carefully.

Regards,
Task Force
"""

        message.set_content(body)


        # ====================================================
        # SEND EMAIL
        # ====================================================

        print(f"Sending email to {employee_email}...")

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

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
            f"Email failed for {employee_email}: {exc}"
        )

        return False