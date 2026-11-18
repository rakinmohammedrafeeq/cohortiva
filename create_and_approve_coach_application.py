#!/usr/bin/env python3
"""
Create and approve a coach application for an existing user.

This is useful when a user registered as Student but wants to become a Coach.
"""

import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from Users.models import Profile, Role, CoachApplication
from Tutoring.models import Tutor


def create_and_approve_coach(email, expertise=None, experience=None, qualifications=None, bio=None):
    """Create a coach application and immediately approve it."""
    
    # Find user
    try:
        user = User.objects.get(email=email)
        print(f"✅ Found user: {user.username} ({user.email})")
    except User.DoesNotExist:
        print(f"❌ No user found with email: {email}")
        return False
    
    # Check existing application
    existing_app = CoachApplication.objects.filter(user=user).first()
    if existing_app:
        if existing_app.status == CoachApplication.STATUS_APPROVED:
            print(f"✅ User already has an approved coach application")
            return True
        elif existing_app.status == CoachApplication.STATUS_PENDING:
            print(f"✅ Found existing pending application, will approve it")
            application = existing_app
        else:
            print(f"⚠️  Found rejected application, creating new one")
            application = None
    else:
        application = None
    
    # Create application if needed
    if not application:
        print(f"📝 Creating new coach application...")
        
        default_expertise = expertise or "Subject matter expert with coaching experience"
        default_experience = experience or "Experienced in mentoring and coaching students"
        default_qualifications = qualifications or "Relevant qualifications and certifications"
        default_bio = bio or f"Coach - {user.get_full_name()}"
        
        application = CoachApplication.objects.create(
            user=user,
            expertise=default_expertise,
            experience=default_experience,
            qualifications=default_qualifications,
            bio=default_bio,
            status=CoachApplication.STATUS_PENDING
        )
        print(f"✅ Created coach application (ID: {application.id})")
    
    # Get or create admin
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        print("⚠️  Creating temporary admin user...")
        admin = User.objects.create_superuser(
            username='admin_system',
            email='admin@cohortiva.local',
            password='admin_temp_pass_123',
            first_name='System',
            last_name='Admin'
        )
        admin_role = Role.get_or_create_role('Admin')
        Profile.objects.get_or_create(
            user=admin,
            defaults={'role': admin_role, 'email_verified': True}
        )
        print(f"✅ Created admin user: {admin.username}")
    else:
        print(f"✅ Using existing admin: {admin.username}")
    
    # Approve application
    print(f"\n🔄 Approving coach application...")
    
    try:
        tutor_role = Role.get_or_create_role('Tutor')
        
        with transaction.atomic():
            # Update application
            application.status = CoachApplication.STATUS_APPROVED
            application.reviewed_by = admin
            application.reviewed_at = timezone.now()
            application.save()
            print(f"  ✓ Application approved")
            
            # Elevate profile role
            profile = user.profile
            profile.role = tutor_role
            profile.save(update_fields=['role'])
            print(f"  ✓ Profile role elevated to Tutor")
            
            # Create Tutor record
            tutor, created = Tutor.objects.update_or_create(
                profile=profile,
                defaults={
                    'expertise': application.expertise,
                    'bio': application.bio,
                }
            )
            print(f"  ✓ Tutor record {'created' if created else 'updated'}")
        
        print(f"\n✅ SUCCESS! {user.username} is now a Coach!")
        print(f"\n📋 Application Details:")
        print(f"   ID: {application.id}")
        print(f"   Status: {application.status}")
        print(f"   Reviewed by: {application.reviewed_by.username}")
        print(f"   Reviewed at: {application.reviewed_at}")
        
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
        print("Usage: python create_and_approve_coach_application.py email [expertise] [experience]")
        sys.exit(1)
    
    email = sys.argv[1]
    expertise = sys.argv[2] if len(sys.argv) > 2 else None
    experience = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("=" * 70)
    print("🎓 Cohortiva - Create and Approve Coach Application")
    print("=" * 70)
    
    # Check database
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("\n❌ DATABASE_URL not set!")
        sys.exit(1)
    
    try:
        from django.db import connection
        connection.ensure_connection()
        print(f"✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Create and approve
    success = create_and_approve_coach(email, expertise, experience)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ DONE - You are now a Coach!")
        print("=" * 70)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
