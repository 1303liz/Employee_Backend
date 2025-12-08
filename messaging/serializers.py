from rest_framework import serializers
from .models import Message, Announcement
from accounts.models import CustomUser


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for message display"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    recipient_details = UserBasicSerializer(source='recipient', read_only=True)
    replies_count = serializers.SerializerMethodField()
    unread_replies_count = serializers.SerializerMethodField()
    has_unread_replies = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_details', 'recipient', 'recipient_details',
            'subject', 'body', 'is_read', 'created_at', 'read_at',
            'parent_message', 'replies_count', 'unread_replies_count', 'has_unread_replies'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at', 'read_at']

    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def get_unread_replies_count(self, obj):
        """Count unread replies where current user is the recipient"""
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        return obj.replies.filter(recipient=request.user, is_read=False).count()
    
    def get_has_unread_replies(self, obj):
        """Check if there are any unread replies for current user"""
        return self.get_unread_replies_count(obj) > 0

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class MessageThreadSerializer(serializers.ModelSerializer):
    """Serializer for message threads with replies"""
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    recipient_details = UserBasicSerializer(source='recipient', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_details', 'recipient', 'recipient_details',
            'subject', 'body', 'is_read', 'created_at', 'read_at',
            'parent_message', 'replies'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at', 'read_at']

    def get_replies(self, obj):
        if obj.parent_message:
            return []
        replies = obj.replies.all().order_by('created_at')
        return MessageSerializer(replies, many=True, context=self.context).data


class AnnouncementSerializer(serializers.ModelSerializer):
    sender_details = UserBasicSerializer(source='sender', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'sender', 'sender_details', 'title', 'content', 'priority', 'created_at', 'is_active']
        read_only_fields = ['sender', 'created_at']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
