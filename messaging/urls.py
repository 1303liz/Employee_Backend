from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, AnnouncementViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),
]
