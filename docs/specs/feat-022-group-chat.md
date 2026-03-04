# FEAT-022: Group Chat per Course

## Status: Done

## Summary
Each course has a group chat room where enrolled members can post and read messages in real time (via HTMX polling).

## Models
- ChatMessage (`apps/notifications/models.py`): academy (FK Academy), sender (FK User), message (TextField). Extends TimeStampedModel. Ordered by `created_at`.

## Views
- CourseChatView (`apps/notifications/views.py`) -- GET renders the chat room with the latest 50 messages (reversed for chronological order); POST creates a new ChatMessage and supports HTMX partial response for the message list.

## URLs
- `/notifications/chat/<slug:slug>/` -- `course-chat`

## Templates
- `templates/notifications/chat_room.html`
- `templates/notifications/partials/_chat_messages.html`

## Tests
- TestGroupChat in `tests/integration/test_release2_features.py` -- chat room loads, post message via POST, message persisted in ChatMessage
