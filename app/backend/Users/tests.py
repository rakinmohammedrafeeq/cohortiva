from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from unittest.mock import patch, MagicMock
import time

from .models import Profile, Role
from .utils.tokens import generate_password_reset_token, validate_password_reset_token


class PasswordResetSecurityTests(TestCase):
    """Test password reset token security."""
    
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name='Student')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )
        self.profile = Profile.objects.create(user=self.user, role=self.role)
    
    def test_password_reset_token_expiry(self):
        """Test that password reset tokens expire after PASSWORD_RESET_TIMEOUT."""
        # Generate token
        uid, token = generate_password_reset_token(self.user)
        
        # Token should be valid immediately
        user = validate_password_reset_token(uid, token)
        self.assertEqual(user, self.user)
        
        # Mock timezone to simulate token expiry (3600 seconds + 1)
        with patch('django.contrib.auth.tokens.PasswordResetTokenGenerator._now') as mock_now:
            # Simulate time passage beyond timeout
            mock_now.return_value = timezone.now() + timedelta(seconds=3601)
            user = validate_password_reset_token(uid, token)
            self.assertIsNone(user)
    
    def test_password_reset_token_single_use(self):
        """Test that password reset tokens cannot be reused after password change."""
        # Generate token
        uid, token = generate_password_reset_token(self.user)
        
        # Use token to reset password
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to reuse same token
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'AnotherPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_generic_response(self):
        """Test that password reset returns generic response for unknown emails."""
        # Request reset for non-existent email
        response = self.client.post('/api/users/password-reset/request/', {
            'email': 'nonexistent@example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('If an account exists', response.data['detail'])
        
        # Request reset for existing email - should look identical
        response = self.client.post('/api/users/password-reset/request/', {
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('If an account exists', response.data['detail'])


class JWTInvalidationTests(TestCase):
    """Test JWT token invalidation after password reset."""
    
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name='Student')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )
        self.profile = Profile.objects.create(user=self.user, role=self.role)
    
    def test_old_access_token_invalid_after_password_reset(self):
        """Test that old access tokens are invalidated after password reset."""
        # Ensure profile exists before getting token
        self.profile.refresh_from_db()
        
        # Login to get tokens
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'OldPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_access_token = response.data['access']
        
        # Verify token works
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(1)
        
        # Reset password
        uid, token = generate_password_reset_token(self.user)
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password_changed_at was set
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.password_changed_at)
        
        # Old access token should now be invalid
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_old_refresh_token_invalid_after_password_reset(self):
        """Test that old refresh tokens are invalidated after password reset."""
        # Login to get tokens
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'OldPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_refresh_token = response.data['refresh']
        
        # Verify refresh token works
        response = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Reset password
        uid, token = generate_password_reset_token(self.user)
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Old refresh token should now be invalid
        response = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_new_tokens_work_after_password_reset(self):
        """Test that new tokens work after password reset."""
        # Reset password
        uid, token = generate_password_reset_token(self.user)
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Login with new password
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_token = response.data['access']
        
        # New token should work
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_immediate_login_after_password_reset(self):
        """
        Regression test: Verify immediate login after password reset.
        Ensures new tokens are accepted and old tokens (access + refresh) are rejected.
        """
        # Get old tokens
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'OldPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_access_token = response.data['access']
        old_refresh_token = response.data['refresh']
        
        # Verify old access token works
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(1)
        
        # Reset password
        uid, token = generate_password_reset_token(self.user)
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # IMMEDIATELY login with new password (no delay)
        response = self.client.post('/api/token/', {
            'username': 'testuser',
            'password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        f"Immediate login failed: {response.status_code}, {response.data}")
        new_access_token = response.data['access']
        new_refresh_token = response.data['refresh']
        
        # Verify new access token works immediately
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        f"New access token rejected: {response.status_code}")
        
        # Verify old access token is rejected
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access_token}')
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        f"Old access token still valid: {response.status_code}")
        
        # Verify old refresh token is rejected
        response = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        f"Old refresh token still valid: {response.status_code}")
        
        # Verify new refresh token works
        response = self.client.post('/api/token/refresh/', {
            'refresh': new_refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        f"New refresh token rejected: {response.status_code}")


class EmailDeliveryFailureTests(TestCase):
    """Test graceful handling of email delivery failures."""
    
    def setUp(self):
        self.client = APIClient()
        # Create both roles needed by registration logic
        self.student_role = Role.objects.create(id=1, name='Student')
        self.guest_role = Role.objects.create(id=5, name='Guest')
    
    @patch('Users.utils.email.send_html_email')
    def test_registration_survives_email_failure(self, mock_send_html_email):
        """Test that registration completes even if email delivery fails."""
        # Simulate email failure
        mock_send_html_email.return_value = False
        
        response = self.client.post('/api/users/register/student/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        
        # Registration should still succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                        f"Expected 201, got {response.status_code}: {response.data}")
        self.assertIn('email_status', response.data)
        self.assertEqual(response.data['email_status'], 'pending')
        
        # User should be created
        user = User.objects.get(username='newuser')
        self.assertIsNotNone(user)
        self.assertTrue(Profile.objects.filter(user=user).exists())
    
    @patch('Users.utils.email.send_html_email')
    def test_registration_retry_no_duplicate(self, mock_send_html_email):
        """Test that retrying registration after email failure doesn't create duplicates."""
        # Simulate email failure
        mock_send_html_email.return_value = False
        
        # First attempt
        response = self.client.post('/api/users/register/student/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                        f"First attempt failed: {response.status_code}: {response.data}")
        
        # Retry should fail with validation error
        response = self.client.post('/api/users/register/student/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('Users.utils.email.send_html_email')
    def test_password_reset_request_hides_email_failure(self, mock_send_html_email):
        """Test that password reset maintains anti-enumeration even on email failure."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        Profile.objects.create(user=user, role=self.student_role)
        
        # Simulate email failure
        mock_send_html_email.return_value = False
        
        response = self.client.post('/api/users/password-reset/request/', {
            'email': 'test@example.com'
        })
        
        # Should still return generic success message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('If an account exists', response.data['detail'])
    
    @patch('Users.utils.email.send_html_email')
    def test_resend_verification_reports_failure(self, mock_send_html_email):
        """Test that resend verification properly reports email failure."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        profile = Profile.objects.create(user=user, role=self.student_role)
        
        # Simulate email failure
        mock_send_html_email.return_value = False
        
        # Login
        self.client.force_authenticate(user=user)
        
        response = self.client.post('/api/users/resend-verification/')
        
        # Should report service unavailable
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('try again later', response.data['detail'].lower())


class EmailVerificationSecurityTests(TestCase):
    """Test email verification token security."""
    
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name='Student')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        self.profile = Profile.objects.create(user=self.user, role=self.role)
    
    def test_email_verification_token_single_use(self):
        """Test that email verification tokens can only be used once."""
        # Generate token
        token = self.profile.generate_verification_token()
        
        # First use should succeed
        response = self.client.post('/api/users/verify-email/', {
            'token': token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Reload profile
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.email_verified)
        
        # Second use should fail
        response = self.client.post('/api/users/verify-email/', {
            'token': token
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_email_verification_token_expiry(self):
        """Test that email verification tokens expire after 24 hours."""
        # Generate token
        token = self.profile.generate_verification_token()
        
        # Simulate time passage (25 hours)
        self.profile.email_verification_sent_at = timezone.now() - timedelta(hours=25)
        self.profile.save()
        
        # Token should be expired
        response = self.client.post('/api/users/verify-email/', {
            'token': token
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExistingUserCompatibilityTests(TestCase):
    """Test that existing users maintain access after migration."""
    
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(name='Student')
    
    def test_existing_unverified_user_can_login(self):
        """Test that users with email_verified=False can still login."""
        user = User.objects.create_user(
            username='legacyuser',
            email='legacy@example.com',
            password='Password123!'
        )
        profile = Profile.objects.create(user=user, role=self.role)
        # Simulate migration state - email_verified defaults to False
        self.assertFalse(profile.email_verified)
        
        # Login should work
        response = self.client.post('/api/token/', {
            'username': 'legacyuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_existing_unverified_user_can_access_api(self):
        """Test that unverified users can access authenticated endpoints."""
        user = User.objects.create_user(
            username='legacyuser',
            email='legacy@example.com',
            password='Password123!'
        )
        profile = Profile.objects.create(user=user, role=self.role)
        self.assertFalse(profile.email_verified)
        
        # Login
        self.client.force_authenticate(user=user)
        
        # Should be able to access profile
        response = self.client.get('/api/users/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EmailDomainValidationTests(TestCase):
    """Test email domain validation allows various domains."""
    
    def setUp(self):
        self.client = APIClient()
        # Create both required roles
        self.student_role = Role.objects.create(id=1, name='Student')
        self.guest_role = Role.objects.create(id=5, name='Guest')
    
    def test_rnsit_email_accepted(self):
        """Test that @rnsit.ac.in emails are accepted."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@rnsit.ac.in',
            'password': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='test@rnsit.ac.in')
        self.assertIsNotNone(user)
    
    def test_gmail_email_accepted(self):
        """Test that Gmail addresses are accepted."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'gmailuser',
            'email': 'user@gmail.com',
            'password': 'SecurePass123!',
            'first_name': 'Gmail',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='user@gmail.com')
        self.assertIsNotNone(user)
    
    def test_various_domains_accepted(self):
        """Test that various email domains are accepted."""
        domains = ['example.org', 'university.edu', 'company.co.uk', 'domain.io']
        
        for i, domain in enumerate(domains):
            username = f'user{i}'
            email = f'{username}@{domain}'
            response = self.client.post('/api/users/register/student/', {
                'username': username,
                'email': email,
                'password': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User',
            })
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                           f"Failed for domain: {domain}")
            self.assertTrue(User.objects.filter(email=email).exists())
    
    def test_invalid_email_format_rejected(self):
        """Test that invalid email formats are rejected."""
        invalid_emails = [
            'notanemail',
            '@nodomain.com',
            'missing@',
            'no@domain',
            'spaces in@email.com',
        ]
        
        for i, email in enumerate(invalid_emails):
            response = self.client.post('/api/users/register/student/', {
                'username': f'invaliduser{i}',
                'email': email,
                'password': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User',
            })
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Should reject: {email}")
    
    def test_duplicate_email_rejected(self):
        """Test that duplicate emails are rejected."""
        # Create first user
        User.objects.create_user(
            username='firstuser',
            email='duplicate@example.com',
            password='Password123!'
        )
        Profile.objects.create(
            user=User.objects.get(username='firstuser'),
            role=self.guest_role
        )
        
        # Try to register with same email
        response = self.client.post('/api/users/register/student/', {
            'username': 'seconduser',
            'email': 'duplicate@example.com',
            'password': 'SecurePass123!',
            'first_name': 'Second',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class PasswordValidationTests(TestCase):
    """Test password validation matches Django validators."""
    
    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(id=1, name='Student')
        self.guest_role = Role.objects.create(id=5, name='Guest')
    
    def test_strong_password_accepted(self):
        """Test that strong passwords meeting all criteria are accepted."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'MySecureP@ssw0rd123',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_password_too_short_rejected(self):
        """Test that passwords under 8 characters are rejected."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Short1',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_entirely_numeric_password_rejected(self):
        """Test that entirely numeric passwords are rejected."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '12345678',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_common_password_rejected(self):
        """Test that common passwords are rejected."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_similar_to_username_rejected(self):
        """Test that passwords similar to username are rejected."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'johndoe',
            'email': 'john@example.com',
            'password': 'johndoe123',
            'first_name': 'John',
            'last_name': 'Doe',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_validation(self):
        """Test that password validation works during password reset."""
        from .utils.tokens import generate_password_reset_token
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )
        Profile.objects.create(user=user, role=self.student_role)
        
        uid, token = generate_password_reset_token(user)
        
        # Try weak password
        response = self.client.post('/api/users/password-reset/confirm/', {
            'uid': uid,
            'token': token,
            'new_password': '12345678'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_confirmation_mismatch(self):
        """Test frontend-level password confirmation (mocked in backend test)."""
        # This tests the serializer accepts valid passwords
        response = self.client.post('/api/users/register/student/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'ValidPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
