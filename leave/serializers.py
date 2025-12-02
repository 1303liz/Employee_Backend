from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import (
    LeaveType, LeaveBalance, LeaveApplication, 
    LeaveApplicationAttachment, LeaveApplicationComment
)
from accounts.serializers import UserSerializer

User = get_user_model()

class LeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for leave types"""
    
    class Meta:
        model = LeaveType
        fields = [
            'id', 'name', 'description', 'max_days_per_year', 
            'requires_approval', 'advance_notice_days', 'is_active', 'created_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
        }

class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for leave balances"""
    leave_type = LeaveTypeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    available_days = serializers.ReadOnlyField()
    utilization_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'user', 'leave_type', 'year', 'total_allocated', 
            'used_days', 'pending_days', 'available_days', 'utilization_percentage'
        ]

class LeaveApplicationAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for leave application attachments"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveApplicationAttachment
        fields = [
            'id', 'file_name', 'file_path', 'file_size', 
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        extra_kwargs = {
            'uploaded_by': {'read_only': True},
            'uploaded_at': {'read_only': True},
        }

class LeaveApplicationCommentSerializer(serializers.ModelSerializer):
    """Serializer for leave application comments"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveApplicationComment
        fields = [
            'id', 'comment', 'is_internal', 'author', 'author_name', 'created_at'
        ]
        extra_kwargs = {
            'author': {'read_only': True},
            'created_at': {'read_only': True},
        }

class LeaveApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for leave applications"""
    employee = UserSerializer(read_only=True)
    leave_type = LeaveTypeSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    replacement_employee = UserSerializer(read_only=True)
    
    # Display fields
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    # Related data
    attachments = LeaveApplicationAttachmentSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    
    # Write-only fields for updates
    leave_type_id = serializers.IntegerField(write_only=True, required=False)
    replacement_employee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_id', 'start_date', 'end_date',
            'total_days', 'reason', 'priority', 'priority_display', 'contact_number',
            'emergency_contact', 'status', 'status_display', 'applied_on',
            'approved_by', 'approved_on', 'approval_comments', 'is_half_day',
            'replacement_employee', 'replacement_employee_id', 'attachments', 'comments'
        ]
        extra_kwargs = {
            'employee': {'read_only': True},
            'applied_on': {'read_only': True},
            'approved_by': {'read_only': True},
            'approved_on': {'read_only': True},
        }
    
    def get_comments(self, obj):
        """Get comments based on user role"""
        user = self.context['request'].user
        comments = obj.comments.all()
        
        # Non-HR users cannot see internal comments
        if not user.is_hr:
            comments = comments.filter(is_internal=False)
        
        return LeaveApplicationCommentSerializer(comments, many=True).data
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type_id = data.get('leave_type_id')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError('End date cannot be before start date.')
            
            if start_date < date.today():
                raise serializers.ValidationError('Cannot apply for leave in the past.')
        
        # Check advance notice if leave type is provided
        if leave_type_id and start_date:
            try:
                leave_type = LeaveType.objects.get(id=leave_type_id)
                required_date = date.today() + timedelta(days=leave_type.advance_notice_days)
                if start_date < required_date:
                    raise serializers.ValidationError(
                        f'This leave type requires {leave_type.advance_notice_days} days advance notice.'
                    )
            except LeaveType.DoesNotExist:
                raise serializers.ValidationError('Invalid leave type.')
        
        return data
    
    def update(self, instance, validated_data):
        leave_type_id = validated_data.pop('leave_type_id', None)
        replacement_employee_id = validated_data.pop('replacement_employee_id', None)
        
        if leave_type_id is not None:
            try:
                leave_type = LeaveType.objects.get(id=leave_type_id)
                instance.leave_type = leave_type
            except LeaveType.DoesNotExist:
                raise serializers.ValidationError({'leave_type_id': 'Invalid leave type ID'})
        
        if replacement_employee_id is not None:
            if replacement_employee_id:
                try:
                    replacement = User.objects.get(id=replacement_employee_id)
                    instance.replacement_employee = replacement
                except User.DoesNotExist:
                    raise serializers.ValidationError({'replacement_employee_id': 'Invalid employee ID'})
            else:
                instance.replacement_employee = None
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class LeaveApplicationListSerializer(serializers.ModelSerializer):
    """List serializer for leave applications"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'employee_name', 'leave_type_name', 'start_date', 'end_date',
            'total_days', 'status', 'status_display', 'priority', 'priority_display',
            'applied_on', 'reason'
        ]

class LeaveApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave applications"""
    leave_type_id = serializers.IntegerField()
    replacement_employee_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = LeaveApplication
        fields = [
            'leave_type_id', 'start_date', 'end_date', 'reason', 'priority',
            'contact_number', 'emergency_contact', 'is_half_day', 'replacement_employee_id'
        ]
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type_id = data.get('leave_type_id')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError('End date cannot be before start date.')
            
            if start_date < date.today():
                raise serializers.ValidationError('Cannot apply for leave in the past.')
        
        # Validate leave type and advance notice
        if leave_type_id:
            try:
                leave_type = LeaveType.objects.get(id=leave_type_id)
                required_date = date.today() + timedelta(days=leave_type.advance_notice_days)
                if start_date < required_date:
                    raise serializers.ValidationError(
                        f'This leave type requires {leave_type.advance_notice_days} days advance notice.'
                    )
            except LeaveType.DoesNotExist:
                raise serializers.ValidationError('Invalid leave type.')
        
        return data
    
    def create(self, validated_data):
        leave_type_id = validated_data.pop('leave_type_id')
        replacement_employee_id = validated_data.pop('replacement_employee_id', None)
        
        leave_type = LeaveType.objects.get(id=leave_type_id)
        
        leave_application = LeaveApplication.objects.create(
            employee=self.context['request'].user,
            leave_type=leave_type,
            **validated_data
        )
        
        if replacement_employee_id:
            try:
                replacement = User.objects.get(id=replacement_employee_id)
                leave_application.replacement_employee = replacement
                leave_application.save()
            except User.DoesNotExist:
                pass
        
        return leave_application

class LeaveApplicationApprovalSerializer(serializers.ModelSerializer):
    """Serializer for HR to approve/reject leave applications"""
    
    class Meta:
        model = LeaveApplication
        fields = ['status', 'approval_comments']
    
    def validate_status(self, value):
        if value not in ['APPROVED', 'REJECTED']:
            raise serializers.ValidationError('Status must be either APPROVED or REJECTED.')
        return value
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        
        instance.status = validated_data['status']
        instance.approval_comments = validated_data.get('approval_comments', '')
        instance.approved_by = self.context['request'].user
        instance.approved_on = timezone.now()
        
        # Store previous status for balance calculation
        instance._previous_status = 'PENDING'
        
        instance.save()
        return instance