import smtplib
import socket
from datetime import datetime

def test_smtp_connection(host, port, use_ssl, username, password):
    print(f"\nTesting connection to {host}:{port} at {datetime.now()}")
    
    try:
        if use_ssl:
            print("Attempting SSL connection...")
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            print("Attempting TLS connection...")
            server = smtplib.SMTP(host, port, timeout=30)
        
        server.ehlo()
        if not use_ssl:
            server.starttls()
            server.ehlo()
        
        server.login(username, password)
        print("✓ Connection successful!")
        server.quit()
        return True
        
    except socket.timeout:
        print("✗ Connection timed out (network/firewall issue)")
    except smtplib.SMTPAuthenticationError:
        print("✗ Authentication failed (wrong credentials)")
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
    return False

# Try multiple configurations
configs = [
    {'host': 'smtp.gmail.com', 'port': 587, 'ssl': False},
    {'host': 'smtp.gmail.com', 'port': 465, 'ssl': True},
    {'host': 'smtp-mail.outlook.com', 'port': 587, 'ssl': False},
    {'host': 'smtp.mail.yahoo.com', 'port': 465, 'ssl': True}
]

for config in configs:
    test_smtp_connection(
        host=config['host'],
        port=config['port'],
        use_ssl=config['ssl'],
        username='dgreatmyke@gmail.com',
        password='Mykel@az14'
    )