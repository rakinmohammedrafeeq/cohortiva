"""
URL configuration for Users project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, RegisterStudentAPIView, FacultyViewSet, 
    MajorViewSet, RoleViewSet, ApplyCoachAPIView, CoachApplicationViewSet,
    verify_email, resend_verification_email,
    password_reset_request, password_reset_validate, password_reset_confirm
)

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'faculties', FacultyViewSet, basename='faculties')
router.register(r'majors', MajorViewSet, basename='majors')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'coach-applications', CoachApplicationViewSet, basename='coach-applications')

urlpatterns = list(router.urls) + [
    path('register/student/', RegisterStudentAPIView.as_view(), name='register-student'),
    path('apply-coach/', ApplyCoachAPIView.as_view(), name='apply-coach'),
    # Email verification
    path('verify-email/', verify_email, name='verify-email'),
    path('resend-verification/', resend_verification_email, name='resend-verification'),
    # Password reset
    path('password-reset/request/', password_reset_request, name='password-reset-request'),
    path('password-reset/validate/', password_reset_validate, name='password-reset-validate'),
    path('password-reset/confirm/', password_reset_confirm, name='password-reset-confirm'),
]