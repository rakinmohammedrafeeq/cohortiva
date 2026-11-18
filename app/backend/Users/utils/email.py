from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, html_template, text_template, context, recipient_email):
    """
    Send HTML email with plain text fallback using django-anymail.

    Args:
        subject: Email subject line
        html_template: Path to HTML template
        text_template: Path to plain text template
        context: Template context dictionary
        recipient_email: Recipient email address

    Returns:
        bool: True if sent successfully, False otherwise

    Raises:
        Exception: Re-raises provider exceptions for diagnosis
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

        # Use EmailMultiAlternatives for better control
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            reply_to=[settings.RESEND_REPLY_TO_EMAIL],
        )
        msg.attach_alternative(html_content, "text/html")

        # Send and capture anymail status
        msg.send(fail_silently=False)

        # Log success with sanitized recipient (first 3 chars + domain)
        recipient_safe = recipient_email[:3] + "***@" + recipient_email.split('@')[1] if '@' in recipient_email else "***"
        logger.info(
            f"Email sent successfully: subject='{subject}' recipient={recipient_safe}"
        )

        # Anymail adds esp_response to the message object after sending
        if hasattr(msg, 'anymail_status'):
            status = msg.anymail_status
            logger.debug(f"Anymail status: message_id={status.message_id}, status={status.status}")

        return True

    except Exception as e:
        # Enhanced diagnostic logging without exposing PII
        exception_class = type(e).__name__
        exception_module = type(e).__module__

        # Extract HTTP status if available (Anymail provider exceptions)
        http_status = None
        if hasattr(e, 'status_code'):
            http_status = e.status_code
        elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            http_status = e.response.status_code

        # Safe recipient logging
        recipient_safe = recipient_email[:3] + "***@" + recipient_email.split('@')[1] if '@' in recipient_email else "***"

        log_details = {
            'exception_class': f"{exception_module}.{exception_class}",
            'subject': subject,
            'recipient': recipient_safe,
        }

        if http_status:
            log_details['http_status'] = http_status

        # Log full exception only at debug level (not in production by default)
        logger.error(
            f"Email delivery failed: {log_details}",
            exc_info=False  # Avoid logging full traceback to production logs
        )
        logger.debug(f"Email exception details: {str(e)}", exc_info=True)

        # Re-raise to allow caller to distinguish delivery failure
        raise

def send_verification_email(user, token):
    """
    Send email verification link.

    Returns:
        bool: True if sent successfully, False if delivery failed

    Raises:
        Exception: Re-raises for diagnosis when delivery fails
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'verification_url': verification_url,
        'expiry_hours': 24,
    }

    try:
        send_html_email(
            subject='Verify your Cohortiva account',
            html_template='emails/verify_email.html',
            text_template='emails/verify_email.txt',
            context=context,
            recipient_email=user.email,
        )
        return True
    except Exception:
        # Re-raise for caller to handle and log appropriately
        raise

def send_password_reset_email(user, reset_url):
    """
    Send password reset link.

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: Re-raises for diagnosis when delivery fails
    """
    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'reset_url': reset_url,
        'expiry_minutes': 60,
    }

    try:
        send_html_email(
            subject='Reset your Cohortiva password',
            html_template='emails/password_reset.html',
            text_template='emails/password_reset.txt',
            context=context,
            recipient_email=user.email,
        )
        return True
    except Exception:
        raise

def send_password_changed_email(user):
    """
    Send password change notification.

    Returns:
        bool: True if sent successfully

    Raises:
        Exception: Re-raises for diagnosis when delivery fails
    """
    context = {
        'user': user,
        'first_name': user.first_name or user.username,
        'change_time': timezone.now(),
    }

    try:
        send_html_email(
            subject='Your Cohortiva password was changed',
            html_template='emails/password_changed.html',
            text_template='emails/password_changed.txt',
            context=context,
            recipient_email=user.email,
        )
        return True
    except Exception:
        raise
