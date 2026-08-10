import os
import smtplib
from email.message import EmailMessage
import ssl

# Environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "").strip()
SENDER_APP_PASSWORD = os.environ.get("SENDER_APP_PASSWORD", "").strip()

def send_roster_email(employee_name, employee_email, week_start, shifts, locations):
    """
    Send roster email to employee
    Returns: True if sent successfully, False otherwise
    """
    try:
        print("=" * 60)
        print("📧 EMAIL FUNCTION STARTED")
        print(f"Sender: {SENDER_EMAIL if SENDER_EMAIL else 'NOT SET'}")
        print(f"Password: {'✅ SET' if SENDER_APP_PASSWORD else '❌ NOT SET'}")
        print(f"Recipient: {employee_email}")
        print(f"Week: {week_start}")
        print("=" * 60)

        # --- VALIDATIONS ---
        if not SENDER_EMAIL:
            print("❌ ERROR: SENDER_EMAIL environment variable is missing!")
            print("💡 Add SENDER_EMAIL in Render Environment Variables")
            return False

        if not SENDER_APP_PASSWORD:
            print("❌ ERROR: SENDER_APP_PASSWORD environment variable is missing!")
            print("💡 Add SENDER_APP_PASSWORD in Render Environment Variables")
            return False

        if not employee_email or not employee_email.strip():
            print("❌ ERROR: Employee email is empty!")
            return False

        if not week_start:
            week_start = "Current Week"

        # Clean data
        employee_email = employee_email.strip()
        employee_name = employee_name.strip() or "Employee"

        # --- BUILD EMAIL ---
        msg = EmailMessage()
        msg["Subject"] = f"✅ Your Work Roster - Week Starting {week_start}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = employee_email

        # Get shifts with defaults
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

        msg.set_content(body)

        # --- SEND EMAIL ---
        print("📤 Connecting to Gmail SMTP...")

        context = ssl.create_default_context()
        
        # Try SSL first (port 465)
        try:
            print("🔐 Trying SSL connection on port 465...")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
                print("✅ Connected to Gmail SSL")
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                print("✅ Login successful")
                server.send_message(msg)
                print(f"✅ EMAIL SENT SUCCESSFULLY to {employee_email}")
                print("=" * 60)
                return True
                
        except Exception as ssl_error:
            print(f"⚠️ SSL failed: {str(ssl_error)[:100]}")
            
            # Try TLS if SSL fails (port 587)
            try:
                print("🔐 Trying TLS connection on port 587...")
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                    server.starttls(context=context)
                    print("✅ Connected to Gmail TLS")
                    server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                    print("✅ Login successful")
                    server.send_message(msg)
                    print(f"✅ EMAIL SENT SUCCESSFULLY to {employee_email}")
                    print("=" * 60)
                    return True
                    
            except Exception as tls_error:
                print(f"⚠️ TLS failed: {str(tls_error)[:100]}")
                print("❌ All connection attempts failed!")
                return False

    except smtplib.SMTPAuthenticationError as auth_error:
        print("=" * 60)
        print("❌ GMAIL AUTHENTICATION ERROR")
        print(f"Error: {auth_error}")
        print("📌 SOLUTION:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Turn ON 2-Step Verification")
        print("3. Go to App Passwords")
        print("4. Generate password for 'Mail' and 'Other'")
        print("5. Copy 16-digit password WITHOUT any spaces")
        print("6. Add to Render Environment Variables")
        print("=" * 60)
        return False

    except smtplib.SMTPException as smtp_error:
        print("=" * 60)
        print("❌ SMTP ERROR")
        print(f"Error: {smtp_error}")
        print("=" * 60)
        return False

    except Exception as unexpected_error:
        print("=" * 60)
        print("❌ UNEXPECTED ERROR")
        print(f"Type: {type(unexpected_error).__name__}")
        print(f"Error: {unexpected_error}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False
