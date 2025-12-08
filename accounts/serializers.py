from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Department, UserDocument


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'employee_id', 'department', 'phone_number', 
            'hire_date', 'is_active', 'date_joined', 'last_login', 'password',
            'profile_photo', 'profile_photo_url', 'date_of_birth', 'address',
            'emergency_contact_name', 'emergency_contact_phone', 'bio', 'must_change_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True},
        }
    
    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
        return None
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Password is required for user creation'})
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Update all fields except password
        for attr, value in validated_data.items():
            # Convert empty strings to None for optional fields
            if value == '' and attr in ['date_of_birth', 'address', 'emergency_contact_name', 
                                         'emergency_contact_phone', 'bio', 'phone_number']:
                value = None
            setattr(instance, attr, value)
        
        # Only update password if provided
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    # Update last_login timestamp
                    from django.utils import timezone
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must provide username and password.')
        
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'employee_id', 'department', 
            'phone_number', 'hire_date'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': False},
        }
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return data
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email address already exists.")
        return value
    
    def validate_employee_id(self, value):
        if value and CustomUser.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError("User with this employee ID already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""
    refresh_token = serializers.CharField(help_text="JWT refresh token to blacklist")


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for employee list view (HR only)"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'full_name', 'employee_id', 
            'department', 'role', 'role_display', 'hire_date', 
            'is_active', 'last_login'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for department management"""
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at']
        extra_kwargs = {
            'created_at': {'read_only': True},
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class FirstTimePasswordChangeSerializer(serializers.Serializer):
    """Serializer for first-time password change (no old password required)"""
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        
        user = self.context['request'].user
        if not user.must_change_password:
            raise serializers.ValidationError("Password change not required for this account.")
        
        return data


class UserDocumentSerializer(serializers.ModelSerializer):
    """Serializer for user documents"""
    document_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'user', 'document_type', 'document_name', 
            'document_file', 'document_file_url', 'description', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user']
    
    def get_document_file_url(self, obj):
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
        return None


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_employees = serializers.IntegerField()
    total_hr = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    recent_logins = serializers.IntegerField()