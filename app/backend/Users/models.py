from django.db import models
from django.contrib.auth.models import User
import secrets
from django.utils import timezone
from datetime import timedelta

class Faculty(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
    
class Major(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='majors')
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    @classmethod
    def get_or_create_role(cls, role_name):
        """
        Concurrency-safe helper to get or create a role by name.
        Avoids race conditions and guarantees no duplicate roles under concurrent registration.
        """
        role = cls.objects.filter(name__iexact=role_name).first()
        if role:
            return role
        from django.db import IntegrityError
        try:
            role, _ = cls.objects.get_or_create(name=role_name)
            return role
        except IntegrityError:
            return cls.objects.filter(name__iexact=role_name).first()

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, blank=True, null=True)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, blank=True, null=True)
    student_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Password security fields
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    def generate_verification_token(self):
        """Generate a secure random token for email verification."""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token
    
    def is_verification_token_valid(self, token):
        """Check if verification token is valid and not expired."""
        if not self.email_verification_token or self.email_verification_token != token:
            return False
        if not self.email_verification_sent_at:
            return False
        # Token expires after 24 hours
        expiry_time = self.email_verification_sent_at + timedelta(hours=24)
        return timezone.now() < expiry_time
    
    def verify_email(self, token):
        """Verify email with token."""
        if self.is_verification_token_valid(token):
            self.email_verified = True
            self.email_verification_token = None  # One-time use
            self.email_verification_sent_at = None
            self.save()
            return True
        return False

    def __str__(self):
        sid = f" - {self.student_id}" if self.student_id else ""
        return f"{self.user.username} ({self.role}){sid}"


class CoachApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach_application')
    expertise = models.TextField(help_text="Areas of expertise or subject domains")
    experience = models.TextField(help_text="Relevant coaching or teaching experience")
    qualifications = models.TextField(blank=True, default="", help_text="Certifications, degrees, or credentials")
    bio = models.TextField(blank=True, default="", help_text="Short bio / introduction")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_coach_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CoachApplication: {self.user.username} ({self.status})"
