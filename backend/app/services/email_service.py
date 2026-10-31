import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger("brightloop.email")

async def send_reset_password_email(to_email: str, token: str) -> None:
    reset_url = f"{settings.CORS_ORIGINS[0]}/reset-password?token={token}"
    subject = "Reset your Brightloop password"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1e293b;">Brightloop Password Reset</h2>
        <p>You requested a password reset. Click the button below to reset your password. This link is valid for 30 minutes and can only be used once.</p>
        <div style="margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500;">Reset Password</a>
        </div>
        <p style="color: #64748b; font-size: 14px;">If you did not request this, you can safely ignore this email.</p>
        <p style="color: #94a3b8; font-size: 12px;">Token: {token}</p>
    </div>
    """
    logger.info("Password reset link generated for %s: %s", to_email, reset_url)
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        # Send via localhost SMTP (e.g. Mailhog or dev server)
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=3)
        server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
        server.quit()
        logger.info("Sent password reset email to %s via SMTP", to_email)
    except Exception as e:
        logger.warning("Could not dispatch email via SMTP (Mailhog may be offline), logged link to console: %s", e)
