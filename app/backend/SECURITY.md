# Authentication Security Documentation

## Overview

This document describes the security measures implemented in Cohortiva's authentication system.

## JWT Token Invalidation

### Implementation

**Dual-layer token invalidation on password reset:**

1. **Immediate Access Token Invalidation**
   - `password_changed_at` timestamp added to Profile model
   - Timestamp embedded in JWT claims during token generation
   - Custom `CustomJWTAuthentication` checks token `iat` (issued at) against `password_changed_at`
   - Tokens issued before password change are rejected with `InvalidToken` exception

2. **Refresh Token Blacklisting**
   - SimpleJWT's token blacklist enabled via `rest_framework_simplejwt.token_blacklist`
   - All outstanding refresh tokens blacklisted on password reset
   - `ROTATE_REFRESH_TOKENS=True` and `BLACKLIST_AFTER_ROTATION=True` configured

### Behavior

- Old access tokens: **Immediately invalid** after password reset
- Old refresh tokens: **Blacklisted** and cannot generate new access tokens
- New tokens: Work normally after password reset with new password

### Testing

Run: `python manage.py test Users.tests.JWTInvalidationTests`

Tests verify:
- Old access tokens rejected after password reset
- Old refresh tokens rejected after password reset
- New tokens work after password reset

## Email Delivery Failure Handling

### Implementation

All email-sending operations wrapped in try-except blocks:

1. **Registration** (`RegisterStudentAPIView`)
   - User created first, then email attempted
   - Email failure does not rollback user creation
   - Response includes `email_status: 'pending'` or `'sent'`
   - User can request verification later via `/resend-verification/`

2. **Password Reset Request** (`password_reset_request`)
   - Always returns generic success message (anti-enumeration)
   - Email failures logged but not exposed to client
   - Rate limiting (3/hour per IP) prevents abuse

3. **Resend Verification** (`resend_verification_email`)
   - Returns 503 Service Unavailable on email failure
   - User can retry after rate limit (1 minute)
   - Token generated even if email fails (no orphaned state)

4. **Password Reset Confirmation** (`password_reset_confirm`)
   - Password change succeeds even if confirmation email fails
   - Email failure logged but does not affect password reset success
   - User can verify password change by logging in

### Error Handling

- Exceptions caught: `Exception` (all email provider errors)
- Logging: Errors logged with email address but never with tokens/passwords
- User-facing messages: Generic, no technical details or stack traces
- Status codes: 503 for resend failures, 200 for password reset (don't reveal email status)

### Testing

Run: `python manage.py test Users.tests.EmailDeliveryFailureTests`

Tests use mocked `send_mail` to simulate failures.

## Password Reset Token Security

### Configuration

```python
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
```

### Token Properties

- **Expiry**: 1 hour (3600 seconds)
- **Algorithm**: Django's `PasswordResetTokenGenerator`
- **Hash includes**: `user.pk`, `user.password`, `timestamp`, `email_verified` status
- **Single-use**: Token invalidated when password changes (hash includes `user.password`)
- **Anti-enumeration**: Generic responses for known and unknown emails

### Rate Limiting

Password reset requests: **3 per hour per IP** (`@ratelimit` decorator)

### Testing

Run: `python manage.py test Users.tests.PasswordResetSecurityTests`

Tests verify:
- Token expiry after PASSWORD_RESET_TIMEOUT
- Token cannot be reused after password change
- Generic responses maintain anti-enumeration

## Email Verification Token Security

### Token Properties

- **Expiry**: 24 hours
- **Generation**: `secrets.token_urlsafe(32)` (cryptographically secure)
- **Storage**: `Profile.email_verification_token` (unique constraint)
- **Single-use**: Token cleared on successful verification
- **Validation**: Checks token value and expiry timestamp

### Rate Limiting

Resend verification: **1 per minute per user** (application-level check)

### Testing

Run: `python manage.py test Users.tests.EmailVerificationSecurityTests`

Tests verify:
- Tokens can only be used once
- Tokens expire after 24 hours

## Email Link Security

### URL Construction

- All URLs use `settings.FRONTEND_URL` (never hardcoded)
- Verification URL: `{FRONTEND_URL}/verify-email/{token}`
- Password reset URL: `{FRONTEND_URL}/reset-password/{uid}/{token}`

### Production Requirements

**FRONTEND_URL must be HTTPS in production:**
- Settings validate FRONTEND_URL starts with `https://` when `DEBUG=False`
- Warning raised if HTTP URL configured in production

### Security Headers

Custom `SecurityHeadersMiddleware` adds:
- `Referrer-Policy: no-referrer` (prevents token leakage via referrer)
- `X-Content-Type-Options: nosniff` (prevents MIME sniffing)
- `X-Frame-Options: DENY` (prevents clickjacking)

### HTTPS Enforcement

When `DEBUG=False`:
- `SECURE_SSL_REDIRECT=True` (redirect HTTP to HTTPS)
- `SECURE_PROXY_SSL_HEADER` configured for reverse proxy
- `SESSION_COOKIE_SECURE=True` (HTTPS-only cookies)
- `CSRF_COOKIE_SECURE=True` (HTTPS-only CSRF)
- HSTS enabled (1 year, includeSubDomains, preload)

### Best Practices

1. **Never log complete token-bearing URLs**
   - Log email address and action, not token values
   - Example: ✅ `"Verification email sent to user@example.com"`
   - Example: ❌ `"Verification URL: https://app.com/verify/{token}"`

2. **Avoid third-party scripts on token pages**
   - No analytics on `/verify-email/` or `/reset-password/` pages
   - Tokens never exposed to third-party JavaScript

3. **Token transmission**
   - Verification token: In URL (unavoidable for email links)
   - Password reset validation/confirmation: In POST body
   - Never in query parameters for API calls

## Existing User Compatibility

### Migration Behavior

Migration `0003_profile_email_verification_sent_at_and_more.py`:
- Adds `email_verified = BooleanField(default=False)`
- All existing profiles get `email_verified=False` after migration
- No data loss or access restrictions

### Access Policy

**Current behavior: Non-blocking**
- Users with `email_verified=False` can log in
- Users with `email_verified=False` can access all authenticated endpoints
- Email verification is optional, not enforced

### Requesting Verification

Existing users can verify email:
1. Login normally
2. Call `POST /api/users/resend-verification/` (authenticated)
3. Check email and follow link
4. Status updates to `email_verified=True`

### Future Considerations

To enforce email verification:
1. Add `@permission_classes([IsEmailVerified])` to protected views
2. Update login response to include `email_verified` status
3. Frontend checks status and prompts verification if needed
4. Provide grace period for existing users

**Important**: Do not enable enforcement without:
- Communication plan for existing users
- Grace period implementation
- Testing with production data volume

### Testing

Run: `python manage.py test Users.tests.ExistingUserCompatibilityTests`

Tests verify unverified users maintain full access.

## Deployment Checklist

Before deploying security fixes:

### Environment Variables

Verify in Render dashboard:
- ✅ `FRONTEND_URL=https://cohortiva.vercel.app` (HTTPS required)
- ✅ `RESEND_API_KEY` (from Resend dashboard)
- ✅ `RESEND_FROM_EMAIL` (verified domain)
- ✅ `DEBUG=False`
- ✅ `SECRET_KEY` (strong random key)
- ✅ `DATABASE_URL` (Neon PostgreSQL connection string)

### Migrations

Run migrations on Render:
```bash
python manage.py migrate
```

Expected output includes:
```
Running migrations:
  Applying Users.0004_profile_password_changed_at... OK
```

Check status:
```bash
python manage.py showmigrations Users
```

Should show:
```
[X] 0003_profile_email_verification_sent_at_and_more
[X] 0004_profile_password_changed_at
```

### Testing

1. Run backend tests:
```bash
python manage.py test Users
```

2. Manual end-to-end tests:
   - Register new account → verify email sent
   - Resend verification → rate limiting works
   - Password reset request → email received
   - Password reset confirm → old tokens invalid
   - Login after password reset → new tokens work

### Monitoring

After deployment, monitor logs for:
- Email delivery failures (should be graceful, no crashes)
- Token invalidation working (no unauthorized access after password reset)
- No security warnings about HTTP FRONTEND_URL

### Rollback Plan

If issues arise:
1. Settings changes can be reverted via environment variables (no code deploy needed)
2. Migration `0004` is safe to rollback (adds nullable field, no data loss)
3. Old authentication still works (JWT standard claims unchanged)

## Security Audit Results

### Issues Resolved

1. ✅ **JWT invalidation after password reset**
   - Dual-layer: Access token immediate + refresh token blacklist
   - Tested with automated suite

2. ✅ **Email delivery failure handling**
   - All email operations wrapped with error handling
   - No user creation rollback on email failure
   - Generic responses maintain security

3. ✅ **Password reset timeout**
   - Explicitly set to 3600 seconds (1 hour)
   - Tested with token expiry tests

4. ✅ **Existing user compatibility**
   - Non-blocking email verification
   - All existing users maintain access
   - Tests verify legacy behavior

5. ✅ **Email link security**
   - HTTPS validation in production
   - Security headers middleware
   - Referrer policy prevents token leakage

### Remaining Considerations

1. **Email verification enforcement**
   - Currently optional (non-blocking)
   - Consider enforcement policy for production
   - Requires communication plan for existing users

2. **Logging and monitoring**
   - Email delivery failures logged
   - Monitor failure rates in production
   - Alert on sustained SMTP failures

3. **Token rotation**
   - Refresh tokens rotate on use (SimpleJWT configured)
   - Consider shorter access token lifetime if needed
   - Current: 60min access, 7day refresh

## Testing

### Run All Security Tests

```bash
cd app/backend
python manage.py test Users.tests
```

### Run Specific Test Classes

```bash
# JWT invalidation
python manage.py test Users.tests.JWTInvalidationTests

# Password reset security
python manage.py test Users.tests.PasswordResetSecurityTests

# Email delivery failures
python manage.py test Users.tests.EmailDeliveryFailureTests

# Email verification security
python manage.py test Users.tests.EmailVerificationSecurityTests

# Existing user compatibility
python manage.py test Users.tests.ExistingUserCompatibilityTests
```

### Expected Results

All tests should pass:
```
Ran XX tests in X.XXXs

OK
```

Any failures indicate security issues that must be resolved before deployment.
