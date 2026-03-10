import hashlib
from django.conf import settings
from livekit import api as livekit_api


def generate_room_name(academy_slug, session_id):
    """Generate a deterministic room name for a LiveKit session."""
    raw = f"{academy_slug}-{session_id}-{settings.SECRET_KEY}"
    hash_suffix = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"mla-{academy_slug}-{hash_suffix}"


def generate_access_token(room_name, participant_identity, participant_name, is_instructor=False):
    """Generate a LiveKit JWT access token for a participant."""
    token = livekit_api.AccessToken(
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    token.with_identity(participant_identity)
    token.with_name(participant_name)

    grant = livekit_api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
    if is_instructor:
        grant.room_admin = True
        grant.room_record = True

    token.with_grants(grant)
    return token.to_jwt()


def get_livekit_config(session, user):
    """Generate LiveKit configuration for a video room session."""
    is_instructor = session.instructor == user
    participant_name = user.get_full_name() or user.email
    participant_identity = f"user-{user.pk}"

    token = generate_access_token(
        room_name=session.room_name,
        participant_identity=participant_identity,
        participant_name=participant_name,
        is_instructor=is_instructor,
    )

    return {
        "wsUrl": settings.LIVEKIT_URL,
        "token": token,
        "roomName": session.room_name,
        "isInstructor": is_instructor,
        "startMuted": not is_instructor,
        "participantName": participant_name,
    }


async def start_recording(room_name, filepath):
    """Start a composite recording of the room via LiveKit Egress."""
    lkapi = livekit_api.LiveKitAPI(
        settings.LIVEKIT_URL,
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    try:
        s3_output = livekit_api.S3Upload(
            access_key=getattr(settings, 'R2_ACCESS_KEY_ID', ''),
            secret=getattr(settings, 'R2_SECRET_ACCESS_KEY', ''),
            bucket=getattr(settings, 'R2_BUCKET_NAME', ''),
            endpoint=getattr(settings, 'R2_ENDPOINT_URL', ''),
            region='auto',
            filepath=filepath,
        )
        request = livekit_api.RoomCompositeEgressRequest(
            room_name=room_name,
            file_outputs=[livekit_api.EncodedFileOutput(
                file_type=livekit_api.EncodedFileType.MP4,
                s3=s3_output,
            )],
        )
        result = await lkapi.egress.start_room_composite_egress(request)
        return result.egress_id
    finally:
        await lkapi.aclose()


async def stop_recording(egress_id):
    """Stop an active egress recording."""
    lkapi = livekit_api.LiveKitAPI(
        settings.LIVEKIT_URL,
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
    )
    try:
        await lkapi.egress.stop_egress(livekit_api.StopEgressRequest(egress_id=egress_id))
    finally:
        await lkapi.aclose()
