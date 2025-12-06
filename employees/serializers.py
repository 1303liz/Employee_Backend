from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, Position, EmployeeDocument, EmployeeNote
from accounts.serializers import UserSerializer
from .email_utils import send_temporary_password_email

User = get_user_model()

class PositionSerializer(serializers.ModelSerializer):
    """Serializer for job positions"""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'level', 'level_display', 'created_at']
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Serializer for employee documents"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'title', 
            'file_path', 'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        extra_kwargs = {
            'uploaded_by': {'read_only': True},
            'uploaded_at': {'read_only': True},
        }

class EmployeeNoteSerializer(serializers.ModelSerializer):
    """Serializer for employee notes"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)
    
    class Meta:
        model = EmployeeNote
        fields = [
            'id', 'note', 'note_type', 'note_type_display', 'is_confidential',
            'author', 'author_name', 'created_at'
        ]
        extra_kwargs = {
            'author': {'read_only': True},
            'created_at': {'read_only': True},
        }

class EmployeeProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for employee profile"""
    user = UserSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    position_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    supervisor = UserSerializer(read_only=True)
    supervisor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Display fields
    full_name = serializers.CharField(read_only=True)
    is_active_employee = serializers.BooleanField(read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    # Related data
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    notes = EmployeeNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'position', 'position_id', 'supervisor', 'supervisor_id',
            'date_of_birth', 'gender', 'gender_display', 'emergency_contact_name',
            'emergency_contact_phone', 'address', 'salary', 'employment_type',
            'employment_type_display', 'status', 'status_display', 'termination_date',
            'full_name', 'is_active_employee', 'documents', 'notes',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def update(self, instance, validated_data):
        position_id = validated_data.pop('position_id', None)
        supervisor_id = validated_data.pop('supervisor_id', None)
        
        if position_id is not None:
            try:
                position = Position.objects.get(id=position_id)
                instance.position = position
            except Position.DoesNotExist:
                raise serializers.ValidationError({'position_id': 'Invalid position ID'})
        
        if supervisor_id is not None:
            try:
                supervisor = User.objects.get(id=supervisor_id, role='HR')
                instance.supervisor = supervisor
            except User.DoesNotExist:
                raise serializers.ValidationError({'supervisor_id': 'Invalid supervisor ID or supervisor is not HR'})
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class EmployeeProfileListSerializer(serializers.ModelSerializer):
    """List serializer for employee profiles"""
    user = UserSerializer(read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_active_employee = serializers.BooleanField(read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'position_title', 'supervisor_name', 'full_name',
            'employment_type', 'employment_type_display', 'status', 'status_display',
            'is_active_employee', 'created_at', 'updated_at'
        ]

class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new employee with user account"""
    # User fields
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    department = serializers.CharField(required=False, allow_blank=True, write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    # Employee profile fields
    position_id = serializers.IntegerField(required=False, allow_null=True)
    supervisor_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'department', 'phone_number', 'position_id', 'supervisor_id', 
            'date_of_birth', 'gender', 'emergency_contact_name', 
            'emergency_contact_phone', 'address', 'salary', 
            'employment_type', 'status'
        ]
        read_only_fields = ['id']
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def to_representation(self, instance):
        """Convert the employee profile to a proper response format"""
        data = EmployeeProfileDetailSerializer(instance).data
        
        # Add email status if available
        if hasattr(instance, '_email_sent'):
            data['email_sent'] = instance._email_sent
        if hasattr(instance, '_temporary_password'):
            data['temporary_password'] = instance._temporary_password
        
        return data
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'role': 'EMPLOYEE'
        }
        
        # Extract optional user fields
        if 'department' in validated_data:
            user_data['department'] = validated_data.pop('department')
        if 'phone_number' in validated_data:
            user_data['phone_number'] = validated_data.pop('phone_number')
            
        password = validated_data.pop('password')
        
        # Handle position and supervisor
        position_id = validated_data.pop('position_id', None)
        supervisor_id = validated_data.pop('supervisor_id', None)
        
        # Create user
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.must_change_password = True  # Require password change on first login
        user.save()
        
        # Create employee profile
        employee_profile = EmployeeProfile.objects.create(
            user=user,
            **validated_data
        )
        
        # Set position and supervisor
        if position_id:
            try:
                position = Position.objects.get(id=position_id)
                employee_profile.position = position
            except Position.DoesNotExist:
                pass
        
        if supervisor_id:
            try:
                supervisor = User.objects.get(id=supervisor_id, role='HR')
                employee_profile.supervisor = supervisor
            except User.DoesNotExist:
                pass
        
        employee_profile.save()
        
        # Send temporary password email
        employee_full_name = f"{user.first_name} {user.last_name}"
        email_sent = send_temporary_password_email(
            employee_email=user.email,
            employee_name=employee_full_name,
            username=user.username,
            temporary_password=password
        )
        
        # Store email status in a custom attribute for the response
        employee_profile._email_sent = email_sent
        employee_profile._temporary_password = password
        
        return employee_profile