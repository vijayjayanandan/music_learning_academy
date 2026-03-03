import hashlib
from django.conf import settings


def generate_jitsi_room_name(academy_slug, session_id):
    raw = f"{academy_slug}-{session_id}-{settings.SECRET_KEY}"
    hash_suffix = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"mla-{academy_slug}-{hash_suffix}"


def get_jitsi_config(session, user):
    is_instructor = session.instructor == user
    return {
        "roomName": session.jitsi_room_name,
        "domain": settings.JITSI_DOMAIN,
        "userInfo": {
            "displayName": user.get_full_name() or user.username,
            "email": user.email,
        },
        "configOverwrite": {
            "startWithAudioMuted": not is_instructor,
            "startWithVideoMuted": False,
            "disableDeepLinking": True,
            "prejoinPageEnabled": True,
            "disableAP": True,
            "disableAEC": True,
            "disableNS": True,
            "disableAGC": True,
            "disableHPF": True,
            "stereo": True,
            "opusMaxAverageBitrate": 510000,
        },
        "interfaceConfigOverwrite": {
            "TOOLBAR_BUTTONS": [
                "microphone", "camera", "closedcaptions", "desktop",
                "fullscreen", "fodeviceselection", "hangup", "chat",
                "raisehand", "videoquality", "filmstrip", "tileview",
            ],
            "SHOW_JITSI_WATERMARK": False,
            "SHOW_WATERMARK_FOR_GUESTS": False,
            "DEFAULT_REMOTE_DISPLAY_NAME": "Student",
            "TOOLBAR_ALWAYS_VISIBLE": True,
        },
    }
