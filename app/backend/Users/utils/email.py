from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, html_template, text_template, context, recipient_email):
    """
    Send HTML email with plain text fallback.
    
    Args:
        subject: Email subject line
        html_template: Path to HTML template
        text_template: Path to plain text template
        context: Template context dictionary
        recipient_email: Recipient email address
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Add common context variables
        context.update({
            'frontend_url': settings.FRONTEND_URL,
            'reply_to': settings.RESEND_REPLY_TO_EMAIL,
        })
        
        # Render templates
        html_content = render_to_string(html_template, context)
        text_content = render_to_string(text_template, context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient_email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

def send_verification_email(user, token):
    """Send email verification link."""
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
    
    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'verification_url': verification_url,
        'expiry_hours': 24,
    }
    
    return send_html_email(
        subject='Verify your Cohortiva account',
        html_template='emails/verify_email.html',
        text_template='emails/verify_email.txt',
        context=context,
        recipient_email=user.email,
    )

def send_password_reset_email(user, reset_url):
    """Send password reset link."""
    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'reset_url': reset_url,
        'expiry_minutes': 60,
    }
    
    return send_html_email(
        subject='Reset your Cohortiva password',
        html_template='emails/password_reset.html',
        text_template='emails/password_reset.txt',
        context=context,
        recipient_email=user.email,
    )

def send_password_changed_email(user):
    """Send password change notification."""
    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'change_time': timezone.now(),
    }
    
    return send_html_email(
        subject='Your Cohortiva password was changed',
        html_template='emails/password_changed.html',
        text_template='emails/password_changed.txt',
        context=context,
        recipient_email=user.email,
    )
