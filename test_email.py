import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================
# GMAIL SETTINGS
# ============================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Apni Gmail ID yahan likho
SENDER_EMAIL = "hammadsaeed990@gmail.com"

# Apna Gmail APP PASSWORD yahan likho
SENDER_PASSWORD = "glgs cjrp uxwi glhp"


# ============================================================
# EMAIL DETAILS
# ============================================================

RECEIVER_EMAIL = "hammadsaeed990@gmail.com"

SUBJECT = "Employee Roster Test"

MESSAGE = """
Hello,

This is a test email from the Employee Roster Management System.

If you received this email, the Gmail email system is working successfully.

Regards,
Employee Roster Management System
"""


# ============================================================
# SEND EMAIL
# ============================================================

def send_test_email():

    try:

        print("Connecting to Gmail...")

        message = MIMEMultipart()

        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = SUBJECT

        message.attach(
            MIMEText(
                MESSAGE,
                "plain"
            )
        )

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.starttls()

        print("Logging into Gmail...")

        server.login(
            SENDER_EMAIL,
            SENDER_PASSWORD
        )

        print("Sending email...")

        server.sendmail(
            SENDER_EMAIL,
            RECEIVER_EMAIL,
            message.as_string()
        )

        server.quit()

        print()
        print("========================================")
        print("EMAIL SENT SUCCESSFULLY!")
        print("========================================")
        print()
        print("From:", SENDER_EMAIL)
        print("To:", RECEIVER_EMAIL)

    except Exception as error:

        print()
        print("========================================")
        print("EMAIL FAILED!")
        print("========================================")
        print()
        print("Error:", error)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    send_test_email()