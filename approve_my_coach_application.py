#!/usr/bin/env python3
"""
Quick script to approve your own coach application.

Usage:
  $env:DATABASE_URL='your_production_database_url'
  python approve_my_coach_application.py your_email@example.com
"""

import os
import sys
import django

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from Users.models import Profile, Role, CoachApplication
from Tutoring.models import Tutor


def approve_coach_by_email(email):
    """Find and approve coach application by email."""
    
    # Find user by email
    try:
        user = User.objects.get(email=email)
        print(f"✅ Found user: {user.username} ({user.email})")
    except User.DoesNotExist:
        print(f"❌ No user found with email: {email}")
        return False
    
    # Find pending application
    try:
        application = CoachApplication.objects.get(user=user, status=CoachApplication.STATUS_PENDING)
        print(f"✅ Found pending coach application")
    except CoachApplication.DoesNotExist:
        print(f"❌ No pending coach application found for {email}")
        
        # Check if already approved
        try:
            approved_app = CoachApplication.objects.get(user=user, status=CoachApplication.STATUS_APPROVED)
            print(f"ℹ️  Application already approved on {approved_app.reviewed_at}")
            return True
        except CoachApplication.DoesNotExist:
            print(f"ℹ️  No coach application exists for this user")
            return False
    
    # Get or create admin for approval
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        print("⚠️  No admin user found, creating temporary admin for approval...")
        admin = User.objects.create_superuser(
            username='admin_temp',
            email='admin@cohortiva.local',
            password='temp_admin_pass',
            first_name='Admin',
            last_name='System'
        )
        admin_role = Role.get_or_create_role('Admin')
        Profile.objects.get_or_create(
            user=admin,
            defaults={'role': admin_role, 'email_verified': True}
        )
        print(f"✅ Created temporary admin user: {admin.username}")
    else:
        print(f"✅ Using existing admin: {admin.username}")
    
    # Approve application
    print(f"\n🔄 Approving application...")
    
    try:
        tutor_role = Role.get_or_create_role('Tutor')
        
        with transaction.atomic():
            # Update application
            application.status = CoachApplication.STATUS_APPROVED
            application.reviewed_by = admin
            application.reviewed_at = timezone.now()
            application.save()
            print(f"  ✓ Application status: APPROVED")
            
            # Elevate role
            profile = application.user.profile
            profile.role = tutor_role
            profile.save(update_fields=['role'])
            print(f"  ✓ Profile role: Tutor")
            
            # Create Tutor record
            tutor, created = Tutor.objects.update_or_create(
                profile=profile,
                defaults={
                    'expertise': application.expertise,
                    'bio': application.bio or '',
                }
            )
            print(f"  ✓ Tutor record: {'created' if created else 'updated'}")
        
        print(f"\n✅ SUCCESS! Coach application approved for {user.username}")
        print(f"\n💡 Next steps:")
        print(f"   1. Log out of Cohortiva")
        print(f"   2. Log back in")
        print(f"   3. Your role should now show as 'Coach'")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error during approval: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python approve_my_coach_application.py your_email@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    print("=" * 70)
    print("🎓 Cohortiva Coach Application Quick Approval")
    print("=" * 70)
    
    # Check database connection
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("\n❌ DATABASE_URL environment variable not set!")
        print("\nUsage:")
        print("  $env:DATABASE_URL='postgresql://...'")
        print(f"  python approve_my_coach_application.py {email}")
        sys.exit(1)
    
    try:
        from django.db import connection
        connection.ensure_connection()
        print(f"✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Approve
    success = approve_coach_by_email(email)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ DONE - You are now a coach!")
        print("=" * 70)
    else:
        print("\n❌ Approval failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
