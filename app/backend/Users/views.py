from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Profile, Faculty, Major, Role
from .serializers import (
    ProfileSerializer, RegisterSerializer, FacultySerializer, 
    MajorSerializer, RoleSerializer,
    PasswordResetRequestSerializer, PasswordResetValidateSerializer,
    PasswordResetConfirmSerializer
)
from .utils.email import send_verification_email, send_password_reset_email, send_password_changed_email
from .utils.tokens import generate_password_reset_token, validate_password_reset_token
from rest_framework import viewsets as rf_viewsets


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'faculty', 'major']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'id']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        """Get or update the Profile for the current authenticated user."""
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

        profile = getattr(request.user, "profile", None)
        if profile is None:
            default_role = Role.objects.filter(name__iexact="admin").first()
            profile, _ = Profile.objects.get_or_create(
                user=request.user,
                defaults={"role": default_role}
            )

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        serializer = self.get_serializer(profile, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RegisterStudentAPIView(APIView):
    """Public endpoint to register a student user and create a Profile."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user and profile
        profile = serializer.save()
        
        # Generate verification token and attempt to send email
        token = profile.generate_verification_token()
        email_sent = False
        
        try:
            email_sent = send_verification_email(profile.user, token)
        except Exception as e:
            # Log error but don't expose details to user
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email during registration for {profile.user.email}: {e}")
        
        output = ProfileSerializer(profile, context={'request': request})
        response_data = output.data
        
        # Inform user about email status without exposing technical details
        if not email_sent:
            response_data['email_status'] = 'pending'
            response_data['message'] = 'Registration successful. You can request a verification email from your profile.'
        else:
            response_data['email_status'] = 'sent'
            response_data['message'] = 'Registration successful. Please check your email to verify your account.'
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faculty.objects.all().order_by("name")
    serializer_class = FacultySerializer
    permission_classes = [permissions.AllowAny]


class MajorViewSet(rf_viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for listing majors. Supports optional ?faculty=<id> filter."""
    queryset = Major.objects.select_related('faculty').all().order_by('name')
    serializer_class = MajorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            try:
                fid = int(faculty_id)
                qs = qs.filter(faculty_id=fid)
            except ValueError:
                pass
        return qs
    
class RoleViewSet(rf_viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for listing/retrieving roles."""
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = [permissions.AllowAny]



from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Dùng serializer custom để trả thêm thông tin user sau khi login.
    """
    serializer_class = CustomTokenObtainPairSerializer

# Email Verification Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    '''Resend verification email with rate limiting.'''
    profile = request.user.profile
    
    # Check if already verified
    if profile.email_verified:
        return Response(
            {'detail': 'Email already verified.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rate limiting: 1 email per minute
    if profile.email_verification_sent_at:
        time_since_last = timezone.now() - profile.email_verification_sent_at
        if time_since_last < timedelta(minutes=1):
            seconds_remaining = int((timedelta(minutes=1) - time_since_last).total_seconds())
            return Response(
                {'detail': f'Please wait {seconds_remaining} seconds before requesting another email.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
    
    # Generate new token and attempt to send email
    token = profile.generate_verification_token()
    email_sent = False
    
    try:
        email_sent = send_verification_email(request.user, token)
    except Exception as e:
        # Log error but don't expose details to user
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to resend verification email for {request.user.email}: {e}")
    
    if email_sent:
        return Response(
            {'detail': 'Verification email sent.'},
            status=status.HTTP_200_OK
        )
    else:
        # Token was generated but email failed - user can try again after rate limit
        return Response(
            {'detail': 'Could not send verification email at this time. Please try again later.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    '''Verify email with token.'''
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'detail': 'Token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        profile = Profile.objects.get(email_verification_token=token)
        
        if profile.verify_email(token):
            return Response(
                {'detail': 'Email verified successfully.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Profile.DoesNotExist:
        return Response(
            {'detail': 'Invalid token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


# Password Reset Views

@ratelimit(key='ip', rate='3/h', method='POST', block=True)
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    '''Request password reset. Always returns success (prevent enumeration).'''
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    
    # Try to find user and send email, but don't reveal if they exist
    try:
        user = User.objects.get(email=email)
        uid, token = generate_password_reset_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
        
        # Attempt to send email, but log failures silently
        try:
            send_password_reset_email(user, reset_url)
        except Exception as e:
            # Log email failure without exposing to user
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email to {email}: {e}")
            # Continue to generic response - don't reveal email delivery failure
    except User.DoesNotExist:
        # Log attempt but don't reveal to user
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Password reset requested for non-existent email: {email}")
    
    # Always return success (security: prevent email enumeration)
    return Response(
        {'detail': 'If an account exists with this email, a password reset link has been sent.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_validate(request):
    '''Validate password reset token.'''
    serializer = PasswordResetValidateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    uid = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    
    user = validate_password_reset_token(uid, token)
    
    return Response(
        {'valid': user is not None},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    '''Reset password with valid token.'''
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    uid = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    user = validate_password_reset_token(uid, token)
    
    if not user:
        return Response(
            {'detail': 'Invalid or expired reset link.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Update password change timestamp to invalidate existing tokens
    profile = getattr(user, 'profile', None)
    if profile:
        profile.password_changed_at = timezone.now()
        profile.save()
    
    # Blacklist all outstanding refresh tokens for this user
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    try:
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for outstanding_token in outstanding_tokens:
            from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
    except Exception as e:
        # Log but don't fail if blacklist is unavailable
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not blacklist tokens for user {user.id}: {e}")
    
    # Send confirmation email (but don't fail password reset if email fails)
    try:
        send_password_changed_email(user)
    except Exception as e:
        # Log email failure but password reset still succeeded
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send password change notification to {user.email}: {e}")
    
    return Response(
        {'detail': 'Password reset successfully.'},
        status=status.HTTP_200_OK
    )
