from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # optional: owner, description

    def __str__(self):
        return self.name

class RoomMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room')

class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    MESSAGE_TYPES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default=TEXT)
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # basic notification/read marker

    class Meta:
        ordering = ['created_at']
