# FEAT-034: Built-in Tuner

## Status: Done

## Summary
Browser-based chromatic tuner using microphone input via getUserMedia and autocorrelation-based pitch detection. Entirely client-side JavaScript.

## Models
- None (client-side only)

## Views
- TunerView (`apps/music_tools/views.py`) — Renders tuner page. LoginRequiredMixin, no tenant scoping needed.

## URLs
- `/tools/tuner/` — `tuner`

## Templates
- `templates/music_tools/tuner.html` — Contains getUserMedia mic access and autocorrelation pitch detection JavaScript

## Tests
- TestTuner in `tests/integration/test_release4_features.py`
