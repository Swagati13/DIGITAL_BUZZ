from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = router.urls
