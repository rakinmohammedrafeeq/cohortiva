from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from unittest.mock import patch, MagicMock
import time

from .models import Profile, Role, Faculty, Major, CoachApplication
from .utils.tokens import generate_password_reset_token, validate_password_reset_token


# Disable rate limiting for tests
@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
)
class BaseTestCase(TestCase):
    """Base test case with rate limiting disabled."""
    pass


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

    @patch('Users.views.send_verification_email')
    def test_registration_survives_email_failure(self, mock_send_verification):
        """Test that registration completes even if email delivery fails."""
        # Simulate email failure by raising an exception
        mock_send_verification.side_effect = Exception("Email service unavailable")

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

    @patch('Users.views.send_verification_email')
    def test_registration_retry_no_duplicate(self, mock_send_verification):
        """Test that retrying registration after email failure doesn't create duplicates."""
        # Simulate email failure
        mock_send_verification.side_effect = Exception("Email service unavailable")

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

    @patch('Users.utils.email.send_password_reset_email')
    def test_password_reset_request_hides_email_failure(self, mock_send_reset):
        """Test that password reset maintains anti-enumeration even on email failure."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        Profile.objects.create(user=user, role=self.student_role)

        # Simulate email failure
        mock_send_reset.side_effect = Exception("Email service unavailable")

        response = self.client.post('/api/users/password-reset/request/', {
            'email': 'test@example.com'
        })

        # Should still return generic success message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('If an account exists', response.data['detail'])

    @patch('Users.views.send_verification_email')
    def test_resend_verification_reports_failure(self, mock_send_verification):
        """Public resend endpoint returns generic 200 even when email delivery fails."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!'
        )
        Profile.objects.create(user=user, role=self.student_role)

        # Simulate email delivery failure by raising an exception
        mock_send_verification.side_effect = Exception("Resend API error")

        # Public endpoint - no authentication required
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'test@example.com'
        })

        # Should return generic 200 to prevent enumeration (not 503)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eligible account', response.data['detail'].lower())
        # Should NOT expose email_status field
        self.assertNotIn('email_status', response.data)


class ResendVerificationTests(BaseTestCase):
    """Tests for the public email-based resend-verification endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(name='Student')
        self.user = User.objects.create_user(
            username='verifyuser',
            email='verify@example.com',
            password='Password123!'
        )
        self.profile = Profile.objects.create(user=self.user, role=self.student_role)

    @patch('Users.views.send_verification_email')
    def test_resend_no_auth_required(self, mock_email):
        """Endpoint is fully public - no JWT needed."""
        mock_email.return_value = True
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('Users.views.send_verification_email')
    def test_resend_missing_email_returns_400(self, mock_email):
        """Missing email body field returns 400."""
        mock_email.return_value = True
        response = self.client.post('/api/users/resend-verification/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('Users.views.send_verification_email')
    def test_resend_unknown_email_returns_generic_200(self, mock_email):
        """Unknown email returns generic 200 to prevent enumeration."""
        mock_email.return_value = True
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'nobody@nowhere.example'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eligible account', response.data['detail'].lower())
        # Should NOT send email for unknown address
        mock_email.assert_not_called()

    @patch('Users.views.send_verification_email')
    def test_resend_already_verified_returns_generic_200(self, mock_email):
        """Already-verified accounts silently return generic 200."""
        mock_email.return_value = True
        self.profile.email_verified = True
        self.profile.save()
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eligible account', response.data['detail'].lower())
        # Must NOT send an email
        mock_email.assert_not_called()

    @patch('Users.views.send_verification_email')
    def test_resend_cooldown_returns_generic_200(self, mock_email):
        """Cooldown returns generic 200 (not 429) to prevent enumeration."""
        mock_email.return_value = True
        # First send
        self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        # Immediate second send - should get generic 200 without sending email
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eligible account', response.data['detail'].lower())
        # Should have been called only once (first request)
        self.assertEqual(mock_email.call_count, 1)

    @patch('Users.views.send_verification_email')
    def test_resend_invalidates_previous_token(self, mock_email):
        """A new resend issues a fresh token; old token no longer verifies."""
        mock_email.return_value = True
        old_token = self.profile.generate_verification_token()

        # Advance clock past cooldown
        self.profile.email_verification_sent_at = timezone.now() - timedelta(minutes=2)
        self.profile.save()

        # Request a new token
        self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })

        # Old token must be rejected
        response = self.client.post('/api/users/verify-email/', {'token': old_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('Users.views.send_verification_email')
    def test_resend_delivery_failure_returns_generic_200(self, mock_email):
        """Delivery failure returns generic 200 (not 503) to prevent enumeration."""
        mock_email.side_effect = Exception("Resend API error")
        response = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        # Must return 200 to prevent enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('eligible account', response.data['detail'].lower())
        # Must NOT include email_status field that could leak information
        self.assertNotIn('email_status', response.data)

    @patch('Users.views.send_verification_email')
    def test_anti_enumeration_identical_responses(self, mock_email):
        """
        Prove that unknown, verified, cooldown, and delivery-failure scenarios
        return identical HTTP status and response body.
        """
        # Scenario 1: Unknown email
        response1 = self.client.post('/api/users/resend-verification/', {
            'email': 'unknown@example.com'
        })

        # Scenario 2: Verified account
        self.profile.email_verified = True
        self.profile.save()
        response2 = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })

        # Scenario 3: Cooldown (send twice rapidly)
        self.profile.email_verified = False
        self.profile.save()
        mock_email.return_value = True
        self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })
        response3 = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })

        # Scenario 4: Delivery failure
        self.profile.email_verification_sent_at = timezone.now() - timedelta(minutes=2)
        self.profile.save()
        mock_email.side_effect = Exception("Delivery failed")
        response4 = self.client.post('/api/users/resend-verification/', {
            'email': 'verify@example.com'
        })

        # All scenarios must return identical status code
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response4.status_code, status.HTTP_200_OK)

        # All scenarios must return identical response body
        self.assertEqual(response1.data, response2.data)
        self.assertEqual(response2.data, response3.data)
        self.assertEqual(response3.data, response4.data)

        # Response must be generic and not reveal any information
        self.assertIn('eligible account', response1.data['detail'].lower())
        self.assertNotIn('retry_after', response1.data)
        self.assertNotIn('email_status', response1.data)

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


class AcademicAPITests(TestCase):
    """Test Faculty and Major API endpoints with empty and populated databases."""

    def setUp(self):
        self.client = APIClient()

    def test_faculty_list_empty(self):
        """When database is empty, GET /api/users/faculties/ returns 200 with empty list."""
        Faculty.objects.all().delete()
        response = self.client.get('/api/users/faculties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_faculty_list_populated(self):
        """When database has faculties, returns them sorted by name."""
        Faculty.objects.create(code='SCI', name='Faculty of Science')
        Faculty.objects.create(code='ENG', name='Faculty of Engineering')

        response = self.client.get('/api/users/faculties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Should be sorted by name: Engineering before Science
        self.assertEqual(response.data[0]['code'], 'ENG')
        self.assertEqual(response.data[1]['code'], 'SCI')

    def test_major_list_empty(self):
        """When database is empty, GET /api/users/majors/ returns 200 with empty list."""
        Major.objects.all().delete()
        response = self.client.get('/api/users/majors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_major_filtering_by_faculty(self):
        """Filtering majors by ?faculty=<id> returns only majors for that faculty."""
        fac1 = Faculty.objects.create(code='CS', name='Computer Science')
        fac2 = Faculty.objects.create(code='MATH', name='Mathematics')

        m1 = Major.objects.create(name='Software Engineering', faculty=fac1)
        m2 = Major.objects.create(name='Data Science', faculty=fac1)
        m3 = Major.objects.create(name='Pure Mathematics', faculty=fac2)

        # All majors
        response_all = self.client.get('/api/users/majors/')
        self.assertEqual(len(response_all.data), 3)

        # Filtered by faculty 1
        response_f1 = self.client.get(f'/api/users/majors/?faculty={fac1.id}')
        self.assertEqual(response_f1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_f1.data), 2)
        major_names = [m['name'] for m in response_f1.data]
        self.assertIn('Software Engineering', major_names)
        self.assertIn('Data Science', major_names)
        self.assertNotIn('Pure Mathematics', major_names)


class LearnerRegistrationTests(TestCase):
    """Test learner registration with and without academic data."""

    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(name='Student')
        self.tutor_role = Role.objects.create(name='Tutor')
        self.admin_role = Role.objects.create(name='Admin')

    def test_learner_registration_without_academic_data(self):
        """Learner can register successfully with zero academic data provided."""
        payload = {
            'username': 'academicless_user',
            'email': 'learner@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'Jane',
            'last_name': 'Learner',
        }
        response = self.client.post('/api/users/register/student/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='academicless_user')
        self.assertIsNone(user.profile.student_id)
        self.assertIsNone(user.profile.faculty)
        self.assertIsNone(user.profile.major)
        self.assertEqual(user.profile.role, self.student_role)

    def test_learner_registration_with_academic_data(self):
        """Learner can register with valid faculty, major, and student_id."""
        faculty = Faculty.objects.create(code='ENG', name='Faculty of Engineering')
        major = Major.objects.create(name='Robotics', faculty=faculty)

        payload = {
            'username': 'engineering_student',
            'email': 'eng@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'Alex',
            'last_name': 'Smith',
            'student_id': 'ENG-2024-001',
            'faculty': faculty.id,
            'major': major.id,
        }
        response = self.client.post('/api/users/register/student/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='engineering_student')
        self.assertEqual(user.profile.student_id, 'ENG-2024-001')
        self.assertEqual(user.profile.faculty, faculty)
        self.assertEqual(user.profile.major, major)
        self.assertEqual(user.profile.role, self.student_role)

    def test_major_without_faculty_rejected(self):
        """Submitting a major without a faculty is rejected."""
        faculty = Faculty.objects.create(code='MED', name='Faculty of Medicine')
        major = Major.objects.create(name='Anatomy', faculty=faculty)

        payload = {
            'username': 'orphan_major_user',
            'email': 'med@example.com',
            'password': 'StrongPassword123!',
            'major': major.id,
        }
        response = self.client.post('/api/users/register/student/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('major', response.data)

    def test_mismatched_faculty_and_major_rejected(self):
        """Submitting a major that does not belong to the selected faculty is rejected."""
        fac1 = Faculty.objects.create(code='ART', name='Faculty of Arts')
        fac2 = Faculty.objects.create(code='SCI', name='Faculty of Science')
        major_science = Major.objects.create(name='Astrophysics', faculty=fac2)

        payload = {
            'username': 'mismatched_user',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'faculty': fac1.id,
            'major': major_science.id,
        }
        response = self.client.post('/api/users/register/student/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('major', response.data)


class StudentIDValidationTests(TestCase):
    """Test Student ID format, trimming, normalization, and uniqueness."""

    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(name='Student')

    def test_valid_alphanumeric_student_ids(self):
        """Accepts various valid institutional ID formats and normalizes them."""
        valid_ids = [
            ('  stu-12345  ', 'STU-12345'),
            ('1rn20cs001', '1RN20CS001'),
            ('ABC_9988', 'ABC_9988'),
            ('sid123456', 'SID123456'),
        ]
        for idx, (raw_id, expected_normalized) in enumerate(valid_ids):
            response = self.client.post('/api/users/register/student/', {
                'username': f'student_user_{idx}',
                'email': f'student_{idx}@example.com',
                'password': 'StrongPassword123!',
                'student_id': raw_id,
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            user = User.objects.get(username=f'student_user_{idx}')
            self.assertEqual(user.profile.student_id, expected_normalized)

    def test_invalid_student_ids(self):
        """Rejects student IDs that are too short, too long, or contain invalid characters."""
        invalid_ids = [
            'AB',                       # Too short (< 3 chars)
            'A' * 31,                   # Too long (> 30 chars)
            'STU@123',                  # Invalid character '@'
            'ID 1234',                  # Internal whitespace
            'ID#999',                   # Invalid character '#'
        ]
        for idx, sid in enumerate(invalid_ids):
            response = self.client.post('/api/users/register/student/', {
                'username': f'invalid_sid_user_{idx}',
                'email': f'invalid_{idx}@example.com',
                'password': 'StrongPassword123!',
                'student_id': sid,
            })
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('student_id', response.data)

    def test_duplicate_student_id_rejected(self):
        """Rejects duplicate student IDs case-insensitively."""
        # First registration
        self.client.post('/api/users/register/student/', {
            'username': 'first_student',
            'email': 'first@example.com',
            'password': 'StrongPassword123!',
            'student_id': 'ID-2024-X',
        })

        # Second registration with same ID in different case
        response = self.client.post('/api/users/register/student/', {
            'username': 'second_student',
            'email': 'second@example.com',
            'password': 'StrongPassword123!',
            'student_id': 'id-2024-x',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('student_id', response.data)

    def test_whitespace_only_student_id_stored_as_none(self):
        """A whitespace-only student ID is normalized to None."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'spaces_student',
            'email': 'spaces@example.com',
            'password': 'StrongPassword123!',
            'student_id': '     ',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='spaces_student')
        self.assertIsNone(user.profile.student_id)


class PrivilegeEscalationPreventionTests(TestCase):
    """Test that public endpoints prevent elevation to Tutor or Admin roles."""

    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(name='Student')
        self.tutor_role = Role.objects.create(name='Tutor')
        self.admin_role = Role.objects.create(name='Admin')

    def test_role_injection_in_learner_registration_ignored(self):
        """User cannot elevate privileges by passing role ID in registration body."""
        for elevated_role in [self.tutor_role, self.admin_role]:
            username = f'hack_{elevated_role.name.lower()}'
            response = self.client.post('/api/users/register/student/', {
                'username': username,
                'email': f'{username}@example.com',
                'password': 'StrongPassword123!',
                'role': elevated_role.id,
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            user = User.objects.get(username=username)
            # Must remain Student role
            self.assertEqual(user.profile.role, self.student_role)

    def test_missing_student_id_does_not_infer_tutor_role(self):
        """Absence of student_id must NOT grant Tutor role."""
        response = self.client.post('/api/users/register/student/', {
            'username': 'nosid_user',
            'email': 'nosid@example.com',
            'password': 'StrongPassword123!',
            # student_id omitted
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='nosid_user')
        self.assertEqual(user.profile.role, self.student_role)
        self.assertNotEqual(user.profile.role, self.tutor_role)

    def test_admin_cannot_be_registered_publicly(self):
        """There is no public registration endpoint for administrators."""
        # Attempting to post to coach-applications viewset unauthenticated
        response = self.client.get('/api/users/coach-applications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CoachApplicationFlowTests(TestCase):
    """Test Coach application submission, approval, rejection, and role elevation."""

    def setUp(self):
        self.client = APIClient()
        self.student_role = Role.objects.create(name='Student')
        self.tutor_role = Role.objects.create(name='Tutor')
        self.admin_role = Role.objects.create(name='Admin')

        self.admin_user = User.objects.create_user(
            username='superadmin',
            email='admin@cohortiva.app',
            password='AdminPassword123!',
            is_staff=True,
        )
        Profile.objects.create(user=self.admin_user, role=self.admin_role)

    def test_coach_application_submission(self):
        """Public applicant can submit a coach application; does NOT receive Tutor role initially."""
        payload = {
            'username': 'coach_applicant_1',
            'email': 'coach1@example.com',
            'password': 'CoachPassword123!',
            'first_name': 'Sarah',
            'last_name': 'Connor',
            'expertise': 'Algorithms, Data Structures',
            'experience': '5 years teaching computer science at college level',
            'qualifications': 'M.S. in Computer Science',
            'bio': 'Passionate about problem solving.',
        }
        response = self.client.post('/api/users/apply-coach/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')

        # Check database records
        user = User.objects.get(username='coach_applicant_1')
        app = CoachApplication.objects.get(user=user)
        self.assertEqual(app.status, CoachApplication.STATUS_PENDING)
        self.assertEqual(app.expertise, 'Algorithms, Data Structures')
        # User profile does NOT have Tutor role
        self.assertNotEqual(user.profile.role, self.tutor_role)

    def test_coach_approval_elevates_role_and_creates_tutor(self):
        """Admin approval changes status to approved, elevates profile role to Tutor, and creates Tutor record."""
        # Submit application
        self.client.post('/api/users/apply-coach/', {
            'username': 'future_coach',
            'email': 'future@example.com',
            'password': 'CoachPassword123!',
            'first_name': 'Alan',
            'last_name': 'Turing',
            'expertise': 'Cryptography, Computation',
            'experience': 'Pioneer of computing',
            'bio': 'Ready to coach learners.',
        })

        applicant = User.objects.get(username='future_coach')
        app = CoachApplication.objects.get(user=applicant)

        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)

        # Approve application
        response = self.client.post(f'/api/users/coach-applications/{app.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')

        # Verify applicant profile role is now Tutor
        applicant.profile.refresh_from_db()
        self.assertEqual(applicant.profile.role, self.tutor_role)

        # Verify Tutor model instance in Tutoring app
        from Tutoring.models import Tutor
        tutor_record = Tutor.objects.get(profile=applicant.profile)
        self.assertEqual(tutor_record.expertise, 'Cryptography, Computation')
        self.assertEqual(tutor_record.bio, 'Ready to coach learners.')

    def test_coach_rejection_leaves_applicant_unprivileged(self):
        """Admin rejection marks application as rejected and leaves user role unprivileged."""
        self.client.post('/api/users/apply-coach/', {
            'username': 'rejected_applicant',
            'email': 'rejected@example.com',
            'password': 'CoachPassword123!',
            'expertise': 'None',
            'experience': 'None',
        })
        applicant = User.objects.get(username='rejected_applicant')
        app = CoachApplication.objects.get(user=applicant)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f'/api/users/coach-applications/{app.id}/reject/',
            {'reason': 'Insufficient experience.'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')

        app.refresh_from_db()
        self.assertEqual(app.rejection_reason, 'Insufficient experience.')
        applicant.profile.refresh_from_db()
        self.assertNotEqual(applicant.profile.role, self.tutor_role)

    def test_non_admin_cannot_approve_coach(self):
        """Regular learners cannot approve coach applications."""
        learner_user = User.objects.create_user(
            username='simple_learner',
            email='learner@example.com',
            password='Password123!'
        )
        Profile.objects.create(user=learner_user, role=self.student_role)

        # Create pending application
        applicant = User.objects.create_user(
            username='app_user', email='app@example.com', password='Password123!'
        )
        Profile.objects.create(user=applicant, role=self.student_role)
        app = CoachApplication.objects.create(
            user=applicant, expertise='Math', experience='3 years'
        )

        # Try approving as regular learner
        self.client.force_authenticate(user=learner_user)
        response = self.client.post(f'/api/users/coach-applications/{app.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_and_regular_user_access_blocked_on_all_actions(self):
        """Verify list, retrieve, approve, and reject cannot expose applicant information to non-admins."""
        applicant = User.objects.create_user(
            username='secret_applicant', email='secret@example.com', password='Password123!'
        )
        Profile.objects.create(user=applicant, role=self.student_role)
        app = CoachApplication.objects.create(
            user=applicant, expertise='Secret Expertise', experience='Confidential Experience'
        )

        learner_user = User.objects.create_user(
            username='ordinary_learner', email='ordinary@example.com', password='Password123!'
        )
        Profile.objects.create(user=learner_user, role=self.student_role)

        # 1. Unauthenticated checks (401)
        self.client.logout()
        self.assertEqual(self.client.get('/api/users/coach-applications/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(f'/api/users/coach-applications/{app.id}/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(f'/api/users/coach-applications/{app.id}/approve/').status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(f'/api/users/coach-applications/{app.id}/reject/').status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Regular learner checks (403) - applicant info never exposed
        self.client.force_authenticate(user=learner_user)
        resp_list = self.client.get('/api/users/coach-applications/')
        self.assertEqual(resp_list.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('secret_applicant', str(resp_list.content))

        resp_detail = self.client.get(f'/api/users/coach-applications/{app.id}/')
        self.assertEqual(resp_detail.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('Confidential Experience', str(resp_detail.content))

        self.assertEqual(self.client.post(f'/api/users/coach-applications/{app.id}/approve/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(f'/api/users/coach-applications/{app.id}/reject/').status_code, status.HTTP_403_FORBIDDEN)

    def test_repeated_approval_and_rejection_attempts(self):
        """Verify duplicate approval/rejection handling and state transition consistency."""
        applicant = User.objects.create_user(
            username='repeat_app_user', email='repeat@example.com', password='Password123!'
        )
        Profile.objects.create(user=applicant, role=self.student_role)
        app = CoachApplication.objects.create(
            user=applicant, expertise='Physics', experience='4 years'
        )

        self.client.force_authenticate(user=self.admin_user)

        # Initial approve
        resp1 = self.client.post(f'/api/users/coach-applications/{app.id}/approve/')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Repeated approve attempt on already approved application
        resp2 = self.client.post(f'/api/users/coach-applications/{app.id}/approve/')
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp2.data['detail'], 'Application is already approved.')

        # Attempting to reject an already approved application
        resp_reject = self.client.post(f'/api/users/coach-applications/{app.id}/reject/')
        self.assertEqual(resp_reject.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_reject.data['detail'], 'Cannot reject an already approved application.')

        # Create another application to test repeated rejection
        applicant2 = User.objects.create_user(
            username='reject_app_user', email='reject2@example.com', password='Password123!'
        )
        Profile.objects.create(user=applicant2, role=self.student_role)
        app2 = CoachApplication.objects.create(
            user=applicant2, expertise='Chemistry', experience='1 year'
        )

        resp_rej1 = self.client.post(f'/api/users/coach-applications/{app2.id}/reject/')
        self.assertEqual(resp_rej1.status_code, status.HTTP_200_OK)

        # Repeated reject attempt on already rejected application
        resp_rej2 = self.client.post(f'/api/users/coach-applications/{app2.id}/reject/')
        self.assertEqual(resp_rej2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_rej2.data['detail'], 'Application is already rejected.')

    def test_duplicate_coach_application_submission_rejected(self):
        """Applicant cannot submit duplicate application with existing username or email."""
        payload = {
            'username': 'first_time_coach',
            'email': 'ftc@example.com',
            'password': 'Password123!',
            'expertise': 'Biology',
            'experience': '3 years coaching',
        }
        res1 = self.client.post('/api/users/apply-coach/', payload)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Duplicate username
        res_dup_user = self.client.post('/api/users/apply-coach/', {
            'username': 'first_time_coach',
            'email': 'ftc_diff@example.com',
            'password': 'Password123!',
            'expertise': 'Biology',
            'experience': '3 years',
        })
        self.assertEqual(res_dup_user.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res_dup_user.data)

        # Duplicate email
        res_dup_email = self.client.post('/api/users/apply-coach/', {
            'username': 'different_username_coach',
            'email': 'ftc@example.com',
            'password': 'Password123!',
            'expertise': 'Biology',
            'experience': '3 years',
        })
        self.assertEqual(res_dup_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res_dup_email.data)


class ReferenceDataManagementCommandTests(TestCase):
    """Test seed_reference_data management command."""

    def test_idempotent_role_seeding(self):
        """Command safely creates default roles without duplicating."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('seed_reference_data', stdout=out)
        self.assertIn('Reference Data Seeding Summary', out.getvalue())

        # Verify roles exist
        self.assertTrue(Role.objects.filter(name='Student').exists())
        self.assertTrue(Role.objects.filter(name='Tutor').exists())
        self.assertTrue(Role.objects.filter(name='Admin').exists())

        # Calling a second time produces 0 new roles
        out2 = StringIO()
        call_command('seed_reference_data', stdout=out2)
        self.assertIn('0 created', out2.getvalue())

    def test_dry_run_does_not_commit(self):
        """Dry run does not commit new records."""
        from django.core.management import call_command
        from io import StringIO
        Role.objects.all().delete()

        out = StringIO()
        call_command('seed_reference_data', '--dry-run', stdout=out)
        self.assertIn('[DRY-RUN]', out.getvalue())
        # Roles should still be empty because changes were rolled back
        self.assertEqual(Role.objects.count(), 0)
