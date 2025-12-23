"""
Email service for Citadel Markets Pro
Handles all email sending functionality using SMTP
"""

import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def generate_verification_code():
    """Generate a random 4-digit verification code"""
    return str(random.randint(1000, 9999))


def send_email(to_email, subject, html_content):
    """
    Send HTML email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Email configuration from settings
        smtp_host = settings.EMAIL_HOST
        smtp_port = settings.EMAIL_PORT
        smtp_username = settings.EMAIL_HOST_USER
        smtp_password = settings.EMAIL_HOST_PASSWORD
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = from_email
        message['To'] = to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Connect to SMTP server and send email
        if settings.EMAIL_USE_TLS:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user
    
    Args:
        user: CustomUser instance
    
    Returns:
        bool: Success status
    """
    subject = "Welcome to Citadel Markets Pro! 🎉"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 20px;
                font-weight: 600;
                color: #10b981;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #555;
                margin-bottom: 30px;
            }}
            .features {{
                background-color: #f8fffe;
                border-left: 4px solid #10b981;
                padding: 20px;
                margin: 30px 0;
            }}
            .features h3 {{
                color: #10b981;
                margin-top: 0;
            }}
            .features ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .features li {{
                margin: 8px 0;
                color: #555;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 600;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 30px;
                text-align: center;
                font-size: 14px;
                color: #666;
            }}
            .footer a {{
                color: #10b981;
                text-decoration: none;
            }}
            .divider {{
                height: 1px;
                background-color: #e5e7eb;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Citadel Markets Pro</h1>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hello {user.first_name or 'Trader'}! 👋
                </div>
                
                <div class="message">
                    <p>Welcome to <strong>Citadel Markets Pro</strong> - your gateway to professional trading and investment management!</p>
                    
                    <p>We're thrilled to have you join our community of traders and investors. Your account has been created successfully, and you're now one step closer to achieving your financial goals.</p>
                </div>
                
                <div class="features">
                    <h3>🚀 What's Next?</h3>
                    <ul>
                        <li><strong>Verify your email</strong> to activate your account</li>
                        <li><strong>Complete KYC verification</strong> for full access</li>
                        <li><strong>Explore trading options</strong> - stocks, crypto, forex & more</li>
                        <li><strong>Copy professional traders</strong> and learn from the best</li>
                        <li><strong>Access premium signals</strong> for informed decisions</li>
                    </ul>
                </div>
                
                <div class="divider"></div>
                
                <div class="message">
                    <p><strong>Need help getting started?</strong></p>
                    <p>Our support team is available 24/7 to assist you. Feel free to reach out anytime!</p>
                </div>
                
                <center>
                    <a href="{settings.FRONTEND_URL}/portfolio" class="cta-button">
                        Go to Dashboard →
                    </a>
                </center>
            </div>
            
            <div class="footer">
                <p><strong>Citadel Markets Pro</strong></p>
                <p>Professional Trading & Investment Platform</p>
                <p>
                    <a href="{settings.FRONTEND_URL}/privacy-policy">Privacy Policy</a> | 
                    <a href="{settings.FRONTEND_URL}/terms">Terms of Service</a>
                </p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    This email was sent to {user.email}. If you didn't create this account, please ignore this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_verification_code_email(user, code):
    """
    Send verification code email to user
    
    Args:
        user: CustomUser instance
        code: 4-digit verification code
    
    Returns:
        bool: Success status
    """
    subject = "Your Citadel Markets Pro Verification Code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .greeting {{
                font-size: 20px;
                font-weight: 600;
                color: #10b981;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #555;
                margin-bottom: 30px;
                text-align: left;
            }}
            .code-box {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 3px dashed #10b981;
                border-radius: 10px;
                padding: 30px;
                margin: 30px 0;
            }}
            .code {{
                font-size: 48px;
                font-weight: 700;
                color: #10b981;
                letter-spacing: 15px;
                font-family: 'Courier New', monospace;
            }}
            .code-label {{
                font-size: 14px;
                color: #666;
                margin-top: 10px;
            }}
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 20px 0;
                text-align: left;
            }}
            .warning-title {{
                font-weight: 600;
                color: #f59e0b;
                margin-bottom: 5px;
            }}
            .expiry {{
                font-size: 14px;
                color: #666;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 30px;
                text-align: center;
                font-size: 14px;
                color: #666;
            }}
            .footer a {{
                color: #10b981;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Email Verification</h1>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hello {user.first_name or 'Trader'}!
                </div>
                
                <div class="message">
                    <p>Thank you for registering with Citadel Markets Pro. To complete your account setup, please verify your email address using the code below:</p>
                </div>
                
                <div class="code-box">
                    <div class="code">{code}</div>
                    <div class="code-label">Your Verification Code</div>
                </div>
                
                <div class="expiry">
                    ⏰ This code will expire in <strong>10 minutes</strong>
                </div>
                
                <div class="warning">
                    <div class="warning-title">⚠️ Security Notice</div>
                    <p style="margin: 5px 0; font-size: 14px;">Never share this code with anyone. Citadel Markets Pro staff will never ask for your verification code.</p>
                </div>
                
                <div class="message">
                    <p>If you didn't request this code, please ignore this email or contact our support team immediately.</p>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Citadel Markets Pro</strong></p>
                <p>Professional Trading & Investment Platform</p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    This email was sent to {user.email}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def send_2fa_code_email(user, code):
    """
    Send 2FA login code email to user
    
    Args:
        user: CustomUser instance
        code: 4-digit 2FA code
    
    Returns:
        bool: Success status
    """
    subject = "Your Citadel Markets Pro Login Code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                padding: 40px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .greeting {{
                font-size: 20px;
                font-weight: 600;
                color: #3b82f6;
                margin-bottom: 20px;
            }}
            .message {{
                font-size: 16px;
                color: #555;
                margin-bottom: 30px;
                text-align: left;
            }}
            .code-box {{
                background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border: 3px dashed #3b82f6;
                border-radius: 10px;
                padding: 30px;
                margin: 30px 0;
            }}
            .code {{
                font-size: 48px;
                font-weight: 700;
                color: #3b82f6;
                letter-spacing: 15px;
                font-family: 'Courier New', monospace;
            }}
            .code-label {{
                font-size: 14px;
                color: #666;
                margin-top: 10px;
            }}
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 20px 0;
                text-align: left;
            }}
            .warning-title {{
                font-weight: 600;
                color: #f59e0b;
                margin-bottom: 5px;
            }}
            .expiry {{
                font-size: 14px;
                color: #666;
                margin: 20px 0;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 30px;
                text-align: center;
                font-size: 14px;
                color: #666;
            }}
            .footer a {{
                color: #3b82f6;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Two-Factor Authentication</h1>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Hello {user.first_name or 'Trader'}!
                </div>
                
                <div class="message">
                    <p>A login attempt was detected on your Citadel Markets Pro account. To complete your login, please use the verification code below:</p>
                </div>
                
                <div class="code-box">
                    <div class="code">{code}</div>
                    <div class="code-label">Your 2FA Code</div>
                </div>
                
                <div class="expiry">
                    ⏰ This code will expire in <strong>10 minutes</strong>
                </div>
                
                <div class="warning">
                    <div class="warning-title">⚠️ Security Alert</div>
                    <p style="margin: 5px 0; font-size: 14px;">If you didn't attempt to log in, your account may be compromised. Please change your password immediately and contact our support team.</p>
                </div>
                
                <div class="message">
                    <p><strong>Login Details:</strong></p>
                    <p style="font-size: 14px; color: #666;">
                        Time: {timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')}<br>
                        Email: {user.email}
                    </p>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Citadel Markets Pro</strong></p>
                <p>Professional Trading & Investment Platform</p>
                <p>
                    <a href="{settings.FRONTEND_URL}/settings">Account Settings</a> | 
                    <a href="{settings.FRONTEND_URL}/support">Contact Support</a>
                </p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    This email was sent to {user.email}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user.email, subject, html_content)


def is_code_valid(user):
    """
    Check if verification code is still valid (within 10 minutes)
    
    Args:
        user: CustomUser instance
    
    Returns:
        bool: True if code is valid, False otherwise
    """
    if not user.code_created_at or not user.verification_code:
        return False
    
    expiry_time = user.code_created_at + timedelta(minutes=10)
    return timezone.now() < expiry_time