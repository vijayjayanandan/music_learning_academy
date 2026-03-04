# FEAT-036: Ear Training Exercises

## Status: Done

## Summary
Structured ear training exercises (intervals, chords, rhythm, melody, scales) with JSON-based questions, difficulty levels, and score tracking per student.

## Models
- EarTrainingExercise (`apps/music_tools/models.py`): title, exercise_type (interval/chord/rhythm/melody/scale), difficulty (1-5), questions (JSON), is_active
- EarTrainingScore (`apps/music_tools/models.py`): student (FK User), exercise (FK), score, total_questions, time_taken_seconds; percentage property

## Views
- EarTrainingListView (`apps/music_tools/views.py`) — Lists active exercises for the academy. TenantMixin.
- EarTrainingPlayView (`apps/music_tools/views.py`) — GET renders exercise; POST saves score and redirects back to list.

## URLs
- `/tools/ear-training/` — `ear-training-list`
- `/tools/ear-training/<int:pk>/` — `ear-training-play`

## Templates
- `templates/music_tools/ear_training_list.html`
- `templates/music_tools/ear_training_play.html`

## Tests
- TestEarTraining in `tests/integration/test_release4_features.py`
