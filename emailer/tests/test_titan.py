import smtplib
import ssl

def test_titan_connection():
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            host='smtp.titan.email',
            port=465,
            timeout=30,
            context=context
        ) as server:
            server.login(
                'info@bluediamondsolutions.org',
                '@TheG0lde#Crew'  # Replace with real password
            )
            print("✓ Successfully connected to Titan Email!")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
        return False

if test_titan_connection():
    print("Ready to send emails!")
else:
    print("Please check your settings and try again.")