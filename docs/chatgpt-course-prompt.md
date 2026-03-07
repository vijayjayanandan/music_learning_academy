# ChatGPT Prompt: Generate Music Course Packs

Copy everything below the line into ChatGPT. After it generates a course, paste the output into `apps/courses/course_packs/<course_name>.py`.

---

## PROMPT START

You are a music curriculum designer building course content for a music learning academy platform. Generate a complete course pack as a Python file with two variables: `COURSE` (dict) and `LESSONS` (list of dicts).

### Data Schema

```python
"""<Course Title> — <N>-week <difficulty> course."""

COURSE = {
    "title": str,           # Full course title (e.g. "Piano Foundations — From First Note to First Song")
    "description": str,     # 3-5 sentence course description for the catalog page.
                            # Explain what the student will learn, the approach, and who it's for.
    "instrument": str,      # MUST be one of: "Piano", "Guitar", "Vocals", "Violin", "Drums",
                            #   "Bass Guitar", "Flute", "Saxophone", "Trumpet", "Cello",
                            #   "Tabla", "Sitar", "Veena", "Mridangam", "Ukulele", "Music Theory"
    "genre": str,           # e.g. "Classical", "Jazz", "Rock", "Pop", "Indian Classical",
                            #   "Carnatic", "Blues", "Folk", "" (leave empty if genre-agnostic)
    "difficulty_level": str, # MUST be one of: "beginner", "elementary", "intermediate",
                            #   "upper_intermediate", "advanced"
    "estimated_duration_weeks": int,  # Typically 8-16
    "max_students": int,             # Typically 20-30
    "prerequisites": str,            # What the student needs before starting.
                            # "No prior experience needed." for beginner courses.
    "learning_outcomes": [   # 5-7 specific, measurable outcomes (use action verbs)
        "Play all major scales in two octaves with correct fingering",
        "Read and perform simple sheet music in treble and bass clef",
        # ...
    ],
}

LESSONS = [
    {
        "title": str,        # Lesson title (e.g. "Meeting the Piano — Posture, Hand Position, and Your First Notes")
        "order": int,        # 1-based sequential order
        "description": str,  # 1-2 sentence summary of this lesson
        "estimated_duration_minutes": int,  # Typically 30-60
        "topics": [str],     # 3-6 keyword tags for this lesson (e.g. ["posture", "hand position", "middle C"])
        "content": str,      # FULL lesson content in Markdown (see content guidelines below)
        "assignments": [     # 1-3 assignments per lesson
            {
                "title": str,
                "type": str,  # MUST be one of: "practice", "theory", "ear_training",
                              #   "composition", "performance", "technique"
                "description": str,   # What the student should do (3-5 sentences)
                "practice_minutes_target": int,  # Suggested daily practice time (15-60)
                "tempo_bpm": int or None,  # Optional — only for pieces/exercises with a target tempo
                "instructions": str,  # Optional — day-by-day practice plan or detailed steps
            },
        ],
    },
    # ... more lessons
]
```

### Lesson Content Guidelines

Each lesson's `content` field should be **substantial Markdown** (800-2000 words) that serves as the primary learning material. Include:

1. **Conceptual explanation** — Explain the "why" before the "how". Connect to what the student already knows from previous lessons.

2. **Step-by-step instructions** — Break down the technique or concept into numbered steps. Be specific about physical mechanics (finger placement, breathing, bow angle, etc.).

3. **Markdown tables** where appropriate — for comparing concepts, showing note mappings, chord charts, scale patterns, etc.

4. **Musical examples described in text** — Since we can't embed audio, describe the sound, the feel, the pattern. Reference well-known songs when helpful (e.g., "The first four notes of Beethoven's Fifth...").

5. **Common mistakes section** — 2-3 specific mistakes students make at this stage and how to fix them.

6. **Practice tips** — How to practice this material effectively. Quality over quantity.

7. **Connection to next lesson** — Brief preview of what comes next, so the student sees the progression.

Use Markdown features: `##` headings, `**bold**` for key terms, `|` tables, `-` bullet lists, `>` blockquotes for tips/warnings, `` `code-style` `` for musical notation (e.g., `C-D-E-F-G`).

### Assignment Guidelines

Each lesson should have 1-3 assignments mixing different types:
- **practice**: Hands-on playing/singing exercises with specific goals
- **theory**: Written analysis, notation reading, concept application
- **ear_training**: Listening exercises, interval recognition, pattern identification
- **technique**: Focused drills on specific physical skills (scales, arpeggios, rudiments)
- **composition**: Creative tasks — write a melody, arrange a piece, improvise over changes
- **performance**: Record yourself playing/singing a piece or exercise

### Quality Standards

- **Pedagogically sound**: Follow established teaching progressions for the instrument. Each lesson builds on the previous one. Don't introduce advanced concepts too early.
- **Actionable**: Every lesson should have the student DOING something, not just reading.
- **Specific**: Don't say "practice scales." Say "Practice C major scale, right hand only, ascending and descending, at 60 BPM, 4 times without stopping."
- **Culturally authentic**: For Indian classical music, use correct terminology (raga, tala, swara, not "Indian scale"). For Western music, use standard terminology (measure, bar, time signature).
- **Encouraging tone**: Acknowledge difficulty. Celebrate small wins. Normalize mistakes as part of learning.
- **No placeholder content**: Every lesson must have full, complete content. No "TODO" or "expand later."

### Python File Format Rules

- Use triple-quoted strings (`"""..."""`) for lesson content (Markdown)
- Use parenthesized string concatenation for long single-line strings:
  ```python
  "description": (
      "First part of the description. "
      "Second part continues here."
  ),
  ```
- `tempo_bpm` can be omitted or set to `None` if not applicable
- `instructions` can be omitted if the description is sufficient
- The file must be valid Python — importable with `from apps.courses.course_packs.<name> import COURSE, LESSONS`

### Example (truncated)

```python
"""Hindustani Vocal Foundations — 12-week beginner course."""

COURSE = {
    "title": "Hindustani Vocal Foundations",
    "description": (
        "A structured 12-week introduction to North Indian classical vocal music. "
        "This course takes you from the very first swara to singing a complete bandish "
        "in Raga Yaman. No prior musical experience is required."
    ),
    "instrument": "Vocals",
    "genre": "Indian Classical",
    "difficulty_level": "beginner",
    "estimated_duration_weeks": 12,
    "max_students": 25,
    "prerequisites": "No prior experience needed. A tanpura drone app (free) is required for practice.",
    "learning_outcomes": [
        "Sing all seven shuddha swaras in tune with a tanpura drone",
        "Perform 10 basic alankars with accurate pitch and rhythm",
        "Understand and keep tala using hand claps (Teen Taal — 16 beats)",
        "Sing the aroha/avaroha and pakad of Ragas Yaman and Bhairav",
        "Perform a simple bandish in Raga Yaman with alaap",
        "Identify basic ragas by ear from their characteristic phrases",
    ],
}

LESSONS = [
    {
        "title": "The World of Hindustani Music",
        "order": 1,
        "description": "Introduction to North Indian classical music — its philosophy, structure, and the raga-tala framework.",
        "estimated_duration_minutes": 40,
        "topics": ["Hindustani music", "raga", "tala", "tanpura", "guru-shishya parampara"],
        "content": \"\"\"## Welcome to Hindustani Classical Music

Hindustani classical music is one of the world's oldest and most sophisticated musical
traditions, originating in North India over 2,000 years ago...

### The Two Pillars: Raga and Tala

**Raga** (melody framework): A raga is not simply a scale. It is a set of rules that defines
which notes to use, how to approach them, which phrases are characteristic...

### The Swaras — Notes of Indian Music

| Swara | Full Name | Approximate Western Equivalent |
|-------|-----------|-------------------------------|
| **Sa** | Shadja | Do (C) — the tonic, always fixed |
| **Re** | Rishabh | Re (D) |
...

### Common Mistakes at This Stage

1. **Trying to match a fixed pitch** — Sa is relative to YOUR voice. Don't strain.
2. **Skipping the tanpura** — Always practice with the drone. It trains your ear.\"\"\",
        "assignments": [
            {
                "title": "Find Your Sa",
                "type": "practice",
                "description": (
                    "Download a tanpura app. Experiment with different pitches for Sa "
                    "until you find one where your voice feels relaxed and natural."
                ),
                "practice_minutes_target": 15,
                "instructions": (
                    "Day 1-3: Try different Sa pitches. Sing along and note which feels natural.\\n"
                    "Day 4-7: Lock in your chosen Sa. Sustain it for 5 minutes daily with the tanpura."
                ),
            },
            {
                "title": "Listening — Identify the Tanpura",
                "type": "ear_training",
                "description": (
                    "Listen to any three Hindustani classical performances on YouTube. "
                    "Identify the tanpura drone in the background."
                ),
                "practice_minutes_target": 30,
            },
        ],
    },
    # ... 11 more lessons following the same structure
]
```

---

## NOW GENERATE

Generate a complete course pack for: **[COURSE NAME HERE]**

Requirements:
- **10-14 lessons** with full Markdown content (800-2000 words each)
- **2-3 assignments per lesson** with varied types
- Progressive difficulty — each lesson builds on the previous
- The output must be a single valid Python file I can save and import directly
- Do NOT truncate or abbreviate any lesson content — every lesson must be complete

If the output is too long for one response, stop at a natural lesson boundary and I will say "continue" to get the rest. When continuing, resume the LESSONS list exactly where you left off (keep the list open, don't restart it).
