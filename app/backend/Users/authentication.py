from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.utils import timezone


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that invalidates tokens issued before password change.
    """
    
    def get_user(self, validated_token):
        """
        Override to check if token was issued before password change.
        """
        user = super().get_user(validated_token)
        
        # Check if user has a profile with password_changed_at
        profile = getattr(user, 'profile', None)
        if profile and profile.password_changed_at:
            # Get token issued at timestamp
            token_iat = validated_token.get('iat')
            if token_iat:
                # Convert password_changed_at to timestamp
                pwd_changed_timestamp = int(profile.password_changed_at.timestamp())
                
                # Invalidate token if it was issued before password change
                if token_iat < pwd_changed_timestamp:
                    raise InvalidToken('Token issued before password change')
        
        return user
