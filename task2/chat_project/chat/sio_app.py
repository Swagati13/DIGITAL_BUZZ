# chat/sio_app.py
import json
import asyncio
from django.conf import settings
import socketio
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
from .models import Room, Message, RoomMembership

User = get_user_model()

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
sio_app = socketio.ASGIApp(sio)

# helper to get user from token (SimpleJWT)
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

@sync_to_async
def get_user_from_token(token):
    try:
        validated_token = UntypedToken(token)
    except Exception:
        return None
    # Use simplejwt's authentication backend
    jwt_auth = JWTAuthentication()
    try:
        user, _ = jwt_auth.get_user(validated_token), None
        # Above pattern may differ; instead decode manually:
    except Exception:
        return None
    # Alternatively fetch user id claim
    from rest_framework_simplejwt.backends import TokenBackend
    tb = TokenBackend(algorithm='HS256')
    data = tb.decode(token, verify=False)
    user_id = data.get('user_id') or data.get('user')
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

@sync_to_async
def create_message_in_db(room_id, sender, content=None, message_type='text', image=None):
    room = Room.objects.get(id=room_id)
    msg = Message.objects.create(room=room, sender=sender, content=content or '', message_type=message_type, image=image)
    return msg

@sio.event
async def connect(sid, environ, auth):
    # For socket.io v4, client can send token in auth payload or query string
    # We accept token in query string: ?token=<jwt>
    query_string = environ.get('QUERY_STRING', '')
    qs = parse_qs(query_string)
    token = None
    if 'token' in qs:
        token = qs['token'][0]
    elif auth and isinstance(auth, dict):
        token = auth.get('token')
    user = None
    if token:
        user = await get_user_from_token(token)
    if not user:
        await sio.disconnect(sid)
        return
    # associate SID with user
    await sio.save_session(sid, {'user_id': user.id})
    print(f"User {user.username} connected sid={sid}")

@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    print('disconnect', sid, session)

# join room
@sio.event
async def join_room(sid, data):
    # data: {'room': '<room_id>'}
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return
    room_id = data.get('room')
    await sio.enter_room(sid, room_id)
    # optionally create membership
    await sync_to_async(RoomMembership.objects.get_or_create)(user_id=user_id, room_id=room_id)
    # broadcast notification to room
    await sio.emit('user_joined', {'room': room_id, 'user_id': user_id}, room=room_id)

# leave
@sio.event
async def leave_room(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    room_id = data.get('room')
    await sio.leave_room(sid, room_id)
    await sync_to_async(RoomMembership.objects.filter(user_id=user_id, room_id=room_id).delete)()
    await sio.emit('user_left', {'room': room_id, 'user_id': user_id}, room=room_id)

# send message event
@sio.event
async def send_message(sid, data):
    """
    data: {
        "room": "<room_id>",
        "message_type": "text" / "image",
        "content": "hello",
        "image": null (for image uploads we recommend using REST upload first)
    }
    """
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    if not user_id:
        return

    room_id = data.get('room')
    message_type = data.get('message_type', 'text')
    content = data.get('content')

    # If image is sent as data URL it's heavy — better to upload via REST and send message via socket with image URL
    msg = await create_message_in_db(room_id, User.objects.get(id=user_id), content=content, message_type=message_type)
    # Serialize message for broadcast
    payload = {
        "id": str(msg.id),
        "room": str(msg.room.id),
        "sender": {"id": user_id, "username": await sync_to_async(lambda: User.objects.get(id=user_id).username)()},
        "content": msg.content,
        "message_type": msg.message_type,
        "image": msg.image.url if msg.image else None,
        "created_at": msg.created_at.isoformat()
    }
    await sio.emit('new_message', payload, room=room_id)

