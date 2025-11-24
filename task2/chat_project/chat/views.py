from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Room, Message, RoomMembership
from .serializers import RoomSerializer, MessageSerializer
from django.shortcuts import get_object_or_404

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        room = self.get_object()
        membership, created = RoomMembership.objects.get_or_create(user=request.user, room=room)
        return Response({'joined': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        room = self.get_object()
        RoomMembership.objects.filter(user=request.user, room=room).delete()
        return Response({'left': True}, status=status.HTTP_200_OK)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().select_related('sender')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Accepts text or image POST with room id
        data = request.data.copy()
        data['sender'] = request.user.id
        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        msg = serializer.save(sender=request.user)
        return Response(self.get_serializer(msg, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        q = super().get_queryset()
        room = self.request.query_params.get('room')
        if room:
            q = q.filter(room__id=room)
        return q
