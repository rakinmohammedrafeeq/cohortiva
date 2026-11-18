from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.models import User

class TokenGenerator(PasswordResetTokenGenerator):
    """Custom token generator for password reset."""
    def _make_hash_value(self, user, timestamp):
        # Include email verification status to invalidate token if email changes
        email_verified = getattr(user.profile, 'email_verified', False) if hasattr(user, 'profile') else False
        return f"{user.pk}{user.password}{timestamp}{email_verified}"

token_generator = TokenGenerator()

def generate_password_reset_token(user):
    """
    Generate password reset token and UID.
    
    Returns:
        tuple: (uid, token) both URL-safe strings
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    return uid, token

def validate_password_reset_token(uid, token):
    """
    Validate password reset token and return user.
    
    Args:
        uid: URL-safe base64 encoded user ID
        token: Password reset token
    
    Returns:
        User object if valid, None otherwise
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if token_generator.check_token(user, token):
            return user
        return None
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
