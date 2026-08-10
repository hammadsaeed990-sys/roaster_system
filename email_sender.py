import os
import smtplib
from email.message import EmailMessage
import ssl  # SSL context के लिए

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "").strip()
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "").strip()

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

        # Validation
        if not SENDER_EMAIL:
            print("EMAIL ERROR: SENDER_EMAIL is missing.")
            return False

        if not SENDER_APP_PASSWORD:
            print("EMAIL ERROR: SENDER_APP_PASSWORD is missing.")
            return False

        if not employee_email or not employee_email.strip():
            print("EMAIL ERROR: Employee email is empty.")
            return False

        # Clean up variables
        employee_email = employee_email.strip()
        employee_name = employee_name.strip() or "Employee"

        # Create message
        message = EmailMessage()
        message["Subject"] = f"Your Work Roster - Week Starting {week_start}"
        message["From"] = SENDER_EMAIL
        message["To"] = employee_email

        # Create email body
        body = f"""
Hello {employee_name},

Your work roster has been uploaded successfully.

Week Starting: {week_start}

YOUR ROSTER
-----------
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

        # Create SSL context
        context = ssl.create_default_context()

        # Try both ports if one fails
        smtp_ports = [465, 587]
        
        for port in smtp_ports:
            try:
                if port == 465:
                    # SSL connection
                    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context, timeout=30) as server:
                        print(f"Connected to Gmail SMTP on port {port}")
                        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                        print("Gmail login successful.")
                        server.send_message(message)
                        print(f"EMAIL SENT SUCCESSFULLY TO: {employee_email}")
                        print("==========================================")
                        return True
                else:
                    # TLS connection
                    with smtplib.SMTP("smtp.gmail.com", port, timeout=30) as server:
                        server.starttls(context=context)
                        print(f"Connected to Gmail SMTP on port {port}")
                        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                        print("Gmail login successful.")
                        server.send_message(message)
                        print(f"EMAIL SENT SUCCESSFULLY TO: {employee_email}")
                        print("==========================================")
                        return True
                        
            except Exception as e:
                print(f"Port {port} failed: {str(e)}")
                continue

        print("All ports failed")
        return False

    except smtplib.SMTPAuthenticationError as exc:
        print("==========================================")
        print("GMAIL AUTHENTICATION ERROR")
        print("Error:", exc)
        print("TIPS:")
        print("1. Enable 2FA on Gmail")
        print("2. Generate App Password")
        print("3. Check SENDER_EMAIL is correct")
        print("==========================================")
        return False

    except smtplib.SMTPException as exc:
        print("==========================================")
        print("GMAIL SMTP ERROR")
        print("Error:", exc)
        print("==========================================")
        return False

    except Exception as exc:
        print("==========================================")
        print("EMAIL ERROR")
        print(f"Type: {type(exc).__name__}")
        print(f"Error: {exc!r}")
        import traceback
        traceback.print_exc()
        print("==========================================")
        return False
