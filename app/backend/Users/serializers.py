from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
import re
from .models import Profile, Faculty, Major, Role, CoachApplication

class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "code", "name", "created_at"]

class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ['id', 'name', 'faculty']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'first_name', 'last_name', 'student_id', 'role', 'faculty', 'major', 'created_at'
        ]
        read_only_fields = ['created_at', 'username']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    student_id = serializers.CharField(max_length=50, allow_blank=True, required=False, allow_null=True, default=None)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False, allow_null=True)
    faculty = serializers.PrimaryKeyRelatedField(queryset=Faculty.objects.all(), required=False, allow_null=True)
    major = serializers.PrimaryKeyRelatedField(queryset=Major.objects.all(), required=False, allow_null=True)
    email = serializers.EmailField(allow_blank=False, required=True)

    def validate_username(self, value):
        from django.contrib.auth.models import User
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$', value):
            raise serializers.ValidationError("Username must be 3-30 characters, start with a letter, and contain only letters, numbers, or underscores.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value
    
    def validate_email(self, value):
        from django.contrib.auth.models import User
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
    
    def validate_student_id(self, value):
        if not value:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        normalized = trimmed.upper()
        if not re.match(r'^[A-Z0-9\-_]{3,30}$', normalized):
            raise serializers.ValidationError(
                "Student ID must be between 3 and 30 characters and contain only letters, numbers, hyphens, or underscores."
            )
        from .models import Profile
        if Profile.objects.filter(student_id__iexact=normalized).exists():
            raise serializers.ValidationError("A profile with that student ID already exists.")
        return normalized
    
    def validate_password(self, value):
        '''Validate password against Django password validators.'''
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        # Additional validation: password similarity to username/email
        password = attrs.get('password')
        username = attrs.get('username')
        email = attrs.get('email')
        
        if password and username:
            from django.contrib.auth.models import User
            # Create a temporary user instance for validation (not saved)
            temp_user = User(
                username=username,
                email=email or '',
                first_name=attrs.get('first_name', ''),
                last_name=attrs.get('last_name', '')
            )
            try:
                validate_password(password, user=temp_user)
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        # Validate academic hierarchy
        faculty = attrs.get('faculty')
        major = attrs.get('major')
        if major and not faculty:
            raise serializers.ValidationError({'major': 'A faculty must be selected when specifying a major.'})
        if major and faculty and major.faculty_id != faculty.id:
            raise serializers.ValidationError({'major': 'The selected major does not belong to the selected faculty.'})

        # Always assign Student/Learner role for public learner registration.
        # Ignore any user-supplied role to prevent privilege escalation.
        attrs['role'] = Role.get_or_create_role('Student')

        return attrs

    def create(self, validated_data):
        from django.contrib.auth.models import User
        from django.db import transaction, IntegrityError
        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.pop('email')

        with transaction.atomic():
            user = User(username=username, email=email)
            user.set_password(password)
            user.first_name = validated_data.get('first_name', '')
            user.last_name = validated_data.get('last_name', '')
            user.save()

            profile_data = {
                'user': user,
                'student_id': validated_data.get('student_id', None),
                'role': validated_data.get('role'),
                'faculty': validated_data.get('faculty', None),
                'major': validated_data.get('major', None),
            }

            try:
                profile = Profile.objects.create(**{k: v for k, v in profile_data.items() if v is not None})
            except IntegrityError:
                raise serializers.ValidationError({'student_id': 'A profile with that student ID already exists.'})
        return profile


class CoachApplySerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(allow_blank=False, required=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False, default="")
    expertise = serializers.CharField(required=True, allow_blank=False)
    experience = serializers.CharField(required=True, allow_blank=False)
    qualifications = serializers.CharField(required=False, allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_username(self, value):
        from django.contrib.auth.models import User
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$', value):
            raise serializers.ValidationError("Username must be 3-30 characters, start with a letter, and contain only letters, numbers, or underscores.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        from django.contrib.auth.models import User
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        username = attrs.get('username')
        email = attrs.get('email')
        if password and username:
            from django.contrib.auth.models import User
            temp_user = User(
                username=username,
                email=email or '',
                first_name=attrs.get('first_name', ''),
                last_name=attrs.get('last_name', '')
            )
            try:
                validate_password(password, user=temp_user)
            except DjangoValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        from django.contrib.auth.models import User
        from django.db import transaction
        from .models import CoachApplication

        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        with transaction.atomic():
            user = User(username=username, email=email, first_name=first_name, last_name=last_name)
            user.set_password(password)
            user.save()

            # Ensure Student role for basic learner permissions; DO NOT assign Tutor/Coach privileges
            student_role = Role.get_or_create_role('Student')

            profile = Profile.objects.create(user=user, role=student_role)

            application = CoachApplication.objects.create(
                user=user,
                expertise=validated_data.get('expertise'),
                experience=validated_data.get('experience'),
                qualifications=validated_data.get('qualifications', ''),
                bio=validated_data.get('bio', ''),
                status=CoachApplication.STATUS_PENDING,
            )

        return application


class CoachApplicationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True, default=None)

    class Meta:
        model = CoachApplication
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name',
            'expertise', 'experience', 'qualifications', 'bio',
            'status', 'reviewed_by', 'reviewed_by_username', 'reviewed_at',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']

    

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Trả về thêm thông tin cơ bản của user sau khi login:
    - username, first_name, last_name
    - profile_id
    - role (tên role trong bảng Role)
    - password_changed_at for token invalidation
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Thêm claim cơ bản
        token["username"] = user.username

        # Thêm thông tin từ Profile nếu có
        profile = getattr(user, "profile", None)
        if profile is not None:
            token["profile_id"] = profile.id
            if profile.role:
                token["role"] = profile.role.name
            # Add password change timestamp for token invalidation
            if profile.password_changed_at:
                token["pwd_changed"] = int(profile.password_changed_at.timestamp())

        return token

    def validate(self, attrs):
        """
        Dữ liệu trả về cho FE khi gọi POST /api/token/
        """
        data = super().validate(attrs)
        user = self.user

        data["username"] = user.username
        data["first_name"] = user.first_name
        data["last_name"] = user.last_name

        profile = getattr(user, "profile", None)
        if profile is not None:
            data["profile_id"] = profile.id
            data["email_verified"] = profile.email_verified
            if profile.role:
                data["role"] = profile.role.name

        return data

# Password Reset Serializers

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetValidateSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_new_password(self, value):
        '''Validate password against Django password validators.'''
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
