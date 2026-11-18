#!/usr/bin/env python
"""
Script to approve coach applications directly via database.
Use this for development/testing or when you need to approve your own application.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from Users.models import Profile, CoachApplication, Role
from Tutoring.models import Tutor

def list_pending_applications():
    """List all pending coach applications."""
    pending = CoachApplication.objects.filter(
        status=CoachApplication.STATUS_PENDING
    ).select_related('user').order_by('-created_at')
    
    print("\n" + "="*80)
    print("PENDING COACH APPLICATIONS")
    print("="*80 + "\n")
    
    if not pending.exists():
        print("No pending applications found.\n")
        return []
    
    print(f"Found {pending.count()} pending application(s):\n")
    
    for idx, app in enumerate(pending, 1):
        print(f"Application #{idx}:")
        print(f"  ID: {app.id}")
        print(f"  Username: {app.user.username}")
        print(f"  Email: {app.user.email}")
        print(f"  Name: {app.user.first_name} {app.user.last_name}")
        print(f"  Expertise: {app.expertise}")
        print(f"  Bio: {app.bio[:100]}..." if app.bio and len(app.bio) > 100 else f"  Bio: {app.bio}")
        print(f"  Applied: {app.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
    
    return list(pending)

def approve_application(application, admin_user=None):
    """Approve a coach application and elevate user role."""
    print("\n" + "="*80)
    print("APPROVING COACH APPLICATION")
    print("="*80 + "\n")
    
    print(f"Approving application for: {application.user.username}")
    
    # Ensure Tutor role exists
    tutor_role, created = Role.objects.get_or_create(
        name='Tutor',
        defaults={'name': 'Tutor'}
    )
    if created:
        print("  • Created 'Tutor' role")
    
    with transaction.atomic():
        # Update application status
        application.status = CoachApplication.STATUS_APPROVED
        application.reviewed_by = admin_user
        application.reviewed_at = timezone.now()
        application.save()
        print(f"  ✓ Application status: APPROVED")
        
        # Elevate profile role to Tutor
        profile = application.user.profile
        profile.role = tutor_role
        profile.save()
        print(f"  ✓ User role updated: Learner → Tutor")
        
        # Create or update Tutor record
        tutor, created = Tutor.objects.update_or_create(
            profile=profile,
            defaults={
                'expertise': application.expertise,
                'bio': application.bio or '',
            }
        )
        action = "Created" if created else "Updated"
        print(f"  ✓ Tutor record {action.lower()}")
    
    print("\n✅ SUCCESS! Coach application approved!")
    print(f"\nUser '{application.user.username}' is now a Coach (Tutor role).")
    print("They can now:")
    print("  • Set availability schedules")
    print("  • Receive coaching session bookings")
    print("  • View performance reports\n")

def create_admin_user():
    """Create an admin user for approving applications."""
    print("\n" + "="*80)
    print("CREATE ADMIN USER")
    print("="*80 + "\n")
    
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    if User.objects.filter(username=username).exists():
        print(f"\n⚠️  User '{username}' already exists!")
        user = User.objects.get(username=username)
        if user.is_staff:
            print(f"User '{username}' is already an admin.\n")
            return user
        else:
            response = input("Make this user an admin? (yes/no): ")
            if response.lower() == 'yes':
                user.is_staff = True
                user.is_superuser = True
                user.save()
                print(f"\n✅ User '{username}' is now an admin!\n")
                return user
            else:
                return None
    
    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True
        )
        
        # Create profile with Admin role
        admin_role, _ = Role.objects.get_or_create(name='Admin')
        Profile.objects.create(
            user=user,
            role=admin_role,
            email_verified=True  # Auto-verify admin
        )
    
    print(f"\n✅ Admin user '{username}' created successfully!\n")
    return user

def main():
    """Main workflow."""
    print("\n" + "="*80)
    print("COACH APPLICATION APPROVAL TOOL")
    print("="*80)
    
    # List pending applications
    pending_apps = list_pending_applications()
    
    if not pending_apps:
        print("No applications to approve. Exiting.\n")
        return
    
    print("="*80 + "\n")
    
    # Select application to approve
    if len(pending_apps) == 1:
        selected_app = pending_apps[0]
        print(f"Auto-selecting the only pending application: {selected_app.user.username}")
    else:
        selection = input(f"Select application to approve (1-{len(pending_apps)}) or 'q' to quit: ")
        if selection.lower() == 'q':
            print("\nAborted.\n")
            return
        
        try:
            idx = int(selection) - 1
            selected_app = pending_apps[idx]
        except (ValueError, IndexError):
            print("\n❌ Invalid selection. Aborted.\n")
            return
    
    # Check if we need to create an admin user
    print("\n" + "-"*80 + "\n")
    print("Admin user required to approve applications.")
    
    admin_exists = User.objects.filter(is_staff=True).exists()
    
    if admin_exists:
        print("\nExisting admin users:")
        for admin in User.objects.filter(is_staff=True):
            print(f"  • {admin.username} ({admin.email})")
        
        response = input("\nUse existing admin? (yes/no): ")
        if response.lower() == 'yes':
            admin_username = input("Admin username: ")
            try:
                admin_user = User.objects.get(username=admin_username, is_staff=True)
            except User.DoesNotExist:
                print(f"\n❌ Admin user '{admin_username}' not found.\n")
                return
        else:
            admin_user = create_admin_user()
    else:
        print("No admin users found.")
        response = input("Create admin user now? (yes/no): ")
        if response.lower() == 'yes':
            admin_user = create_admin_user()
        else:
            print("\n❌ Cannot approve without admin user. Aborted.\n")
            return
    
    if not admin_user:
        print("\n❌ Admin user required. Aborted.\n")
        return
    
    # Final confirmation
    print("\n" + "-"*80 + "\n")
    print(f"Ready to approve:")
    print(f"  Application: {selected_app.user.username} ({selected_app.user.email})")
    print(f"  Approved by: {admin_user.username}")
    
    confirmation = input("\nType 'APPROVE' to proceed: ")
    
    if confirmation != 'APPROVE':
        print("\n❌ Confirmation failed. Aborted.\n")
        return
    
    # Approve the application
    approve_application(selected_app, admin_user)
    
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
