import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings


async def send_verification_email(to_email: str, pin: str) -> None:
    settings = get_settings()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "BIU Dorm Exchange - Email Verification"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email

    text = f"Your verification PIN is: {pin}\n\nThis PIN expires in {settings.verification_pin_expiry_minutes} minutes."

    html = f"""\
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
        <h2 style="color: #2563eb; margin-bottom: 8px;">BIU Dorm Exchange</h2>
        <p style="color: #374151; font-size: 14px;">Enter this PIN to verify your email address:</p>
        <div style="background: #eff6ff; border-radius: 12px; padding: 24px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1d4ed8;">{pin}</span>
        </div>
        <p style="color: #6b7280; font-size: 13px;">
            This PIN expires in {settings.verification_pin_expiry_minutes} minutes.
            If you didn't create an account, you can ignore this email.
        </p>
    </div>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, to_email, msg.as_string())
