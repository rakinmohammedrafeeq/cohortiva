#!/usr/bin/env python3
"""Check user and application status."""

import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth.models import User
from Users.models import Profile, CoachApplication

email = sys.argv[1] if len(sys.argv) > 1 else "rakinmohammedrafeeq@gmail.com"

try:
    user = User.objects.get(email=email)
    print(f"✅ User found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.first_name} {user.last_name}")
    print(f"   Is superuser: {user.is_superuser}")
    print(f"   Is staff: {user.is_staff}")
    
    profile = user.profile
    print(f"\n📋 Profile:")
    print(f"   Role: {profile.role.name if profile.role else 'None'}")
    print(f"   Faculty: {profile.faculty}")
    print(f"   Major: {profile.major}")
    print(f"   Student ID: {profile.student_id}")
    print(f"   Email verified: {profile.email_verified}")
    
    # Check for coach application
    print(f"\n🎓 Coach Applications:")
    apps = CoachApplication.objects.filter(user=user).order_by('-created_at')
    
    if apps.exists():
        for app in apps:
            print(f"   - Status: {app.status}")
            print(f"     Created: {app.created_at}")
            print(f"     Expertise: {app.expertise[:100]}...")
            if app.reviewed_at:
                print(f"     Reviewed: {app.reviewed_at} by {app.reviewed_by.username if app.reviewed_by else 'N/A'}")
    else:
        print(f"   ❌ No coach applications found")
        
        # Check if they registered as coach but application wasn't created
        print(f"\n🔍 Checking registration data...")
        from Tutoring.models import Tutor
        
        try:
            tutor = Tutor.objects.get(profile=profile)
            print(f"   ⚠️  Tutor record EXISTS but no CoachApplication!")
            print(f"      This is unusual - user might have been elevated without application")
        except Tutor.DoesNotExist:
            print(f"   No Tutor record found either")

except User.DoesNotExist:
    print(f"❌ No user found with email: {email}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
