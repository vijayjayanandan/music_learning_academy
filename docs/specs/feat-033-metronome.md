# FEAT-033: Built-in Metronome

## Status: Done

## Summary
Browser-based metronome using the Web Audio API. No backend models needed -- entirely client-side JavaScript with AudioContext for precise timing.

## Models
- None (client-side only)

## Views
- MetronomeView (`apps/music_tools/views.py`) — Renders metronome page. LoginRequiredMixin, no tenant scoping needed.

## URLs
- `/tools/metronome/` — `metronome`

## Templates
- `templates/music_tools/metronome.html` — Contains Web Audio API JavaScript with AudioContext for click generation

## Tests
- TestMetronome in `tests/integration/test_release4_features.py`
