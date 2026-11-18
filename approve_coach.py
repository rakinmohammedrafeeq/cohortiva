#!/usr/bin/env python3
"""
Script to approve a pending coach application in production.

This script:
1. Finds pending coach applications
2. Allows you to select which application to approve
3. Approves the application with the same logic as the admin endpoint:
   - Sets status to APPROVED
   - Elevates Profile.role to Tutor
   - Creates Tutor record in Tutoring app
   - Records reviewer and timestamp

Requires: DATABASE_URL environment variable pointing to production Neon PostgreSQL
"""

import os
import sys
import django
from datetime import datetime

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from Users.models import Profile, Role, CoachApplication
from Tutoring.models import Tutor


def list_pending_applications():
    """List all pending coach applications."""
    applications = CoachApplication.objects.filter(
        status=CoachApplication.STATUS_PENDING
    ).select_related('user', 'user__profile').order_by('created_at')
    
    if not applications.exists():
        print("❌ No pending coach applications found.")
        return []
    
    print(f"\n📋 Found {applications.count()} pending application(s):\n")
    
    for idx, app in enumerate(applications, 1):
        print(f"{idx}. User: {app.user.username} ({app.user.email})")
        print(f"   Name: {app.user.first_name} {app.user.last_name}")
        print(f"   Current Role: {app.user.profile.role.name if app.user.profile.role else 'None'}")
        print(f"   Expertise: {app.expertise[:100]}...")
        print(f"   Applied: {app.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    return list(applications)


def get_or_create_admin():
    """Get existing admin user or create one."""
    # Try to find existing admin/superuser
    admin_users = User.objects.filter(is_superuser=True).order_by('id')
    
    if admin_users.exists():
        print(f"\n✅ Found {admin_users.count()} existing admin user(s):")
        for idx, admin in enumerate(admin_users, 1):
            print(f"{idx}. {admin.username} ({admin.email})")
        
        choice = input(f"\nUse admin #{1} for approval? (y/n): ").strip().lower()
        if choice == 'y':
            return admin_users[0]
    
    # Create new admin if needed
    print("\n⚠️  No admin user found or you declined to use existing one.")
    create_new = input("Create a new admin user? (y/n): ").strip().lower()
    
    if create_new != 'y':
        print("❌ Cannot proceed without an admin user.")
        return None
    
    print("\n📝 Creating new admin user...")
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()
    password = input("Admin password: ").strip()
    
    if not username or not email or not password:
        print("❌ All fields are required.")
        return None
    
    try:
        admin = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User'
        )
        
        # Ensure profile exists with Admin role
        admin_role = Role.get_or_create_role('Admin')
        profile, _ = Profile.objects.get_or_create(
            user=admin,
            defaults={'role': admin_role, 'email_verified': True}
        )
        if not profile.role:
            profile.role = admin_role
            profile.email_verified = True
            profile.save()
        
        print(f"✅ Admin user '{username}' created successfully!")
        return admin
    
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return None


def approve_application(application, reviewer):
    """Approve a coach application with the same logic as the admin endpoint."""
    
    if application.status == CoachApplication.STATUS_APPROVED:
        print(f"⚠️  Application for {application.user.username} is already approved.")
        return False
    
    print(f"\n🔄 Approving application for {application.user.username}...")
    
    try:
        # Ensure Tutor role exists (concurrency-safe)
        tutor_role = Role.get_or_create_role('Tutor')
        
        with transaction.atomic():
            # Update application status
            application.status = CoachApplication.STATUS_APPROVED
            application.reviewed_by = reviewer
            application.reviewed_at = timezone.now()
            application.save()
            print(f"  ✓ Application status set to APPROVED")
            
            # Elevate profile role to Tutor
            profile = application.user.profile
            profile.role = tutor_role
            profile.save(update_fields=['role'])
            print(f"  ✓ Profile role elevated to Tutor")
            
            # Create or update Tutor record in Tutoring app
            tutor, created = Tutor.objects.update_or_create(
                profile=profile,
                defaults={
                    'expertise': application.expertise,
                    'bio': application.bio or '',
                }
            )
            action = "created" if created else "updated"
            print(f"  ✓ Tutor record {action}")
        
        print(f"\n✅ Successfully approved application for {application.user.username}!")
        print(f"   - Status: APPROVED")
        print(f"   - Role: Tutor")
        print(f"   - Reviewed by: {reviewer.username}")
        print(f"   - Reviewed at: {application.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n💡 Next steps:")
        print(f"   1. User should log out and log back in")
        print(f"   2. Role should now show as 'Coach' in the dashboard")
        print(f"   3. Coach-specific features should now be accessible")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error approving application: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution function."""
    
    print("=" * 70)
    print("🎓 Cohortiva Coach Application Approval Tool")
    print("=" * 70)
    
    # Check database connection
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print("\n❌ DATABASE_URL environment variable not set!")
            print("\nTo use this script:")
            print("  1. Get DATABASE_URL from Render dashboard")
            print("  2. Run: $env:DATABASE_URL='postgresql://...'; python approve_coach.py")
            return
        
        # Test connection
        from django.db import connection
        connection.ensure_connection()
        print(f"✅ Connected to database: {connection.settings_dict['NAME']}")
    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # List pending applications
    applications = list_pending_applications()
    if not applications:
        return
    
    # Select application to approve
    while True:
        try:
            choice = input(f"\nSelect application # to approve (1-{len(applications)}, or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                print("👋 Exiting without changes.")
                return
            
            idx = int(choice) - 1
            if 0 <= idx < len(applications):
                selected_app = applications[idx]
                break
            else:
                print(f"❌ Invalid choice. Enter a number between 1 and {len(applications)}.")
        except ValueError:
            print("❌ Invalid input. Enter a number or 'q' to quit.")
    
    # Confirm approval
    print(f"\n⚠️  You are about to approve the application for:")
    print(f"   User: {selected_app.user.username} ({selected_app.user.email})")
    print(f"   Name: {selected_app.user.first_name} {selected_app.user.last_name}")
    
    confirm = input("\nProceed with approval? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Approval cancelled.")
        return
    
    # Get or create admin user for reviewer
    admin = get_or_create_admin()
    if not admin:
        return
    
    # Approve the application
    success = approve_application(selected_app, admin)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ APPROVAL COMPLETE")
        print("=" * 70)


if __name__ == '__main__':
    main()
