from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Message, Announcement
from .serializers import MessageSerializer, MessageThreadSerializer, AnnouncementSerializer
from accounts.models import CustomUser


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for handling messages"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient', 'parent_message')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MessageThreadSerializer
        return MessageSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a message and mark as read if user is recipient"""
        instance = self.get_object()
        if instance.recipient == request.user:
            instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get all messages received by the user"""
        messages = self.get_queryset().filter(
            recipient=request.user,
            parent_message__isnull=True  # Only show parent messages
        ).order_by('-created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get all messages sent by the user"""
        messages = self.get_queryset().filter(
            sender=request.user,
            parent_message__isnull=True  # Only show parent messages
        ).order_by('-created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread messages"""
        count = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        if message.recipient != request.user:
            return Response(
                {'error': 'You can only mark your own messages as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        message.mark_as_read()
        return Response({'status': 'Message marked as read'})

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Reply to a message - intelligently determines recipient"""
        parent_message = self.get_object()
        current_user = request.user
        
        # Determine the recipient: it should be "the other person" in the conversation
        # If current user is the sender of the parent message, reply goes to the original recipient
        # If current user is the recipient of the parent message, reply goes to the original sender
        if parent_message.sender == current_user:
            recipient = parent_message.recipient
        else:
            recipient = parent_message.sender
        
        # Get the root message to maintain subject continuity
        root_message = parent_message if not parent_message.parent_message else parent_message.parent_message
        
        # Create reply message
        data = request.data.copy()
        data['parent_message'] = root_message.id  # Always link to root message
        data['recipient'] = recipient.id
        data['subject'] = f"Re: {root_message.subject}" if not root_message.subject.startswith('Re: ') else root_message.subject
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def thread(self, request, pk=None):
        """Get message thread with all replies"""
        message = self.get_object()
        
        # Get the root message (parent) if this is a reply
        root_message = message if not message.parent_message else message.parent_message
        
        # Mark root message as read if user is recipient
        if root_message.recipient == request.user:
            root_message.mark_as_read()
        
        # Mark all unread replies as read where user is recipient
        unread_replies = root_message.replies.filter(
            recipient=request.user,
            is_read=False
        )
        for reply in unread_replies:
            reply.mark_as_read()
        
        serializer = MessageThreadSerializer(root_message, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def contacts(self, request):
        """Get list of users that can be messaged"""
        user = request.user
        
        # Get all users except the current user
        contacts = CustomUser.objects.exclude(id=user.id).order_by('first_name', 'last_name')
        
        # Serialize basic user info
        from .serializers import UserBasicSerializer
        serializer = UserBasicSerializer(contacts, many=True)
        return Response(serializer.data)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """ViewSet for handling announcements"""
    permission_classes = [IsAuthenticated]
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        user = self.request.user
        # HR can see all announcements, employees only see active ones
        if hasattr(user, 'role') and user.role == 'HR':
            return Announcement.objects.all().select_related('sender').order_by('-created_at')
        return Announcement.objects.filter(is_active=True).select_related('sender').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List announcements with proper pagination"""
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Only HR can create announcements"""
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'HR':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only HR can create announcements')
        serializer.save(sender=self.request.user)
    
    def perform_update(self, serializer):
        """Only HR can update announcements"""
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'HR':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only HR can update announcements')
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only HR can delete announcements"""
        if not hasattr(self.request.user, 'role') or self.request.user.role != 'HR':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only HR can delete announcements')
        instance.delete()

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active announcements"""
        announcements = Announcement.objects.filter(
            is_active=True
        ).select_related('sender').order_by('-created_at')
        
        page = self.paginate_queryset(announcements)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)
