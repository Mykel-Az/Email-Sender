# from django.test import TestCase

# Create your tests here.

import smtplib

try:
    with smtplib.SMTP_SSL('smtp.titan.email', 587, timeout=30) as server:
        server.login('info@bluediamondsolutions.org', '@TheG0lde#Crew')
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")