# FEAT-037: Virtual Recital Events

## Status: Done

## Summary
Organize virtual recital events with performer lineup, Jitsi video room integration, public/private visibility, and recording URL support.

## Models
- RecitalEvent (`apps/music_tools/models.py`): title, description, scheduled_start, scheduled_end, status (upcoming/live/completed/cancelled), jitsi_room_name, recording_url, is_public
- RecitalPerformer (`apps/music_tools/models.py`): recital (FK), student (FK User), piece_title, composer, performance_order

## Views
- RecitalListView (`apps/music_tools/views.py`) — Lists all recitals for the academy. TenantMixin.
- RecitalDetailView (`apps/music_tools/views.py`) — Shows recital details and performer lineup.
- RecitalCreateView (`apps/music_tools/views.py`) — Create a recital event. Owner/instructor only. Generates Jitsi room name.

## URLs
- `/tools/recitals/` — `recital-list`
- `/tools/recitals/create/` — `recital-create`
- `/tools/recitals/<int:pk>/` — `recital-detail`

## Templates
- `templates/music_tools/recital_list.html`
- `templates/music_tools/recital_detail.html`
- `templates/music_tools/recital_create.html`

## Tests
- TestVirtualRecitals in `tests/integration/test_release4_features.py`
