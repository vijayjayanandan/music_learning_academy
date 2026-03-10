"""Hindustani Vocal Foundations — 12-week beginner course."""

COURSE = {
    "title": "Hindustani Vocal Foundations",
    "description": (
        "A structured 12-week introduction to North Indian classical vocal music. "
        "This course takes you from the very first swara to singing a complete bandish "
        "in Raga Yaman. You will learn the sargam system, basic alankars, raga grammar, "
        "tala (rhythm cycles), and the art of alaap — the meditative unfolding of a raga. "
        "No prior musical experience is required. All you need is your voice and a tanpura "
        "drone (a free app will do)."
    ),
    "instrument": "Vocals",
    "genre": "Indian Classical",
    "difficulty_level": "beginner",
    "estimated_duration_weeks": 12,
    "max_students": 25,
    "prerequisites": "No prior experience needed. A tanpura drone app (free) is required for practice.",
    "learning_outcomes": [
        "Sing all seven shuddha swaras (Sa Re Ga Ma Pa Dha Ni) in tune with a tanpura drone",
        "Perform 10 basic alankars (melodic patterns) with accurate pitch and rhythm",
        "Understand and keep tala using hand claps (Teen Taal — 16 beats)",
        "Sing the aroha/avaroha and pakad of Ragas Yaman and Bhairav",
        "Perform a simple bandish (composition) in Raga Yaman with alaap",
        "Identify basic ragas by ear from their characteristic phrases",
    ],
}

LESSONS = [
    {
        "title": "The World of Hindustani Music",
        "order": 1,
        "description": "Introduction to North Indian classical music — its philosophy, structure, and the raga-tala framework.",
        "estimated_duration_minutes": 40,
        "topics": [
            "Hindustani music",
            "raga",
            "tala",
            "tanpura",
            "guru-shishya parampara",
        ],
        "content": """## Welcome to Hindustani Classical Music

Hindustani classical music is one of the world's oldest and most sophisticated musical traditions, originating in North India over 2,000 years ago. Unlike Western music which is built on harmony (multiple notes sounding together), Hindustani music is fundamentally **melodic** — it explores the infinite possibilities within a single melodic line.

### The Two Pillars: Raga and Tala

Every performance in Hindustani music rests on two foundations:

**Raga** (melody framework): A raga is not simply a scale. It is a set of rules that defines which notes to use, how to approach them, which phrases are characteristic, what mood to evoke, and even what time of day to perform. There are hundreds of ragas, each with its own personality. You will learn your first raga, Yaman, in Week 6.

**Tala** (rhythm cycle): A tala is a repeating cycle of beats, each with a specific pattern of claps and waves. The most common tala, Teen Taal, has 16 beats divided into 4 groups of 4. You will learn to keep tala in Week 5.

### The Swaras — Notes of Indian Music

Indian music uses seven notes called **swaras**:

| Swara | Full Name | Approximate Western Equivalent |
|-------|-----------|-------------------------------|
| **Sa** | Shadja | Do (C) — the tonic, always fixed |
| **Re** | Rishabh | Re (D) |
| **Ga** | Gandhar | Mi (E) |
| **Ma** | Madhyam | Fa (F) |
| **Pa** | Pancham | Sol (G) — always fixed |
| **Dha** | Dhaivat | La (A) |
| **Ni** | Nishad | Ti (B) |

Unlike Western music where C is always the same frequency, in Hindustani music **Sa can be set to any pitch** that is comfortable for the singer. Everything else is relative to Sa.

### The Tanpura — Your Constant Companion

The tanpura is a drone instrument that continuously sounds Sa and Pa (and sometimes Ma), creating the harmonic bed over which all Hindustani music unfolds. For practice, a tanpura app on your phone works perfectly. Set it to a comfortable Sa for your voice range — typically C# or D for male voices, and A# or B for female voices.

### What You Will Learn

Over 12 weeks, you will progress from singing your first Sa to performing a complete bandish (composition) in Raga Yaman. The journey follows the traditional pedagogical progression:

1. **Swaras** — learning to sing each note in tune
2. **Alankars** — melodic patterns that train your ear and voice
3. **Tala** — rhythmic cycles and timekeeping
4. **Raga** — the art of melodic exploration
5. **Bandish** — structured compositions
6. **Alaap** — free-form raga exploration

Let us begin with the most fundamental act in all of Indian music: singing **Sa**.""",
        "assignments": [
            {
                "title": "Find Your Sa",
                "type": "practice",
                "description": (
                    "Download a tanpura app (iTabla Pro, Tanpura Droid, or any free option). "
                    "Experiment with different pitches for Sa until you find one where your voice "
                    "feels relaxed and natural — not straining high or rumbling low. Once found, "
                    "sing Sa along with the tanpura for 5 minutes, focusing on matching the pitch exactly. "
                    "Notice how your voice 'locks in' with the drone when the pitch is correct."
                ),
                "practice_minutes_target": 15,
                "instructions": (
                    "Day 1-3: Try different Sa pitches (C, C#, D for males; A, A#, B for females). "
                    "Sing along and note which feels most natural.\n"
                    "Day 4-7: Lock in your chosen Sa. Sing and sustain it for 5 minutes daily with the tanpura. "
                    "Close your eyes. Listen more than you sing."
                ),
            },
            {
                "title": "Listening Assignment — Identify the Tanpura",
                "type": "ear_training",
                "description": (
                    "Listen to any three Hindustani classical performances (available on YouTube — "
                    "search for Kishori Amonkar, Bhimsen Joshi, or Ajoy Chakraborty). In each, "
                    "identify the tanpura drone in the background. Notice how it never stops, "
                    "and how the vocalist always returns to Sa."
                ),
                "practice_minutes_target": 30,
            },
        ],
    },
    {
        "title": "Swaras — The Seven Notes",
        "order": 2,
        "description": "Learning to sing each of the seven shuddha (natural) swaras in tune with the tanpura drone.",
        "estimated_duration_minutes": 45,
        "topics": ["swaras", "shuddha swaras", "saptak", "mandra", "madhya", "taar"],
        "content": """## The Seven Shuddha Swaras

Now that you have found your Sa and can sustain it with the tanpura, it is time to learn all seven shuddha (natural/pure) swaras.

### The Three Octaves (Saptaks)

Indian music uses three octave registers:

- **Mandra Saptak** (lower octave) — written with a dot below: Ṣa Ṛe Ga Ma Pa Ḍha Ṇi
- **Madhya Saptak** (middle octave) — written plain: Sa Re Ga Ma Pa Dha Ni — *this is where we start*
- **Taar Saptak** (upper octave) — written with a dot above: Sa' Re' Ga' etc.

### Learning Each Swara

The key to singing swaras in tune is **not** to think of them as fixed pitches to hit, but as **relationships to Sa**. Each swara has a specific emotional and acoustic relationship with the tonic.

**Sa (Shadja)** — The home, the anchor. Every phrase begins and ends here. Sa is stability itself.

**Re (Rishabh)** — A gentle step upward from Sa. Sing Sa, then let your voice rise just slightly. Re should feel like the first ray of morning light — close to Sa, but distinctly separate.

**Ga (Gandhar)** — The third note carries sweetness. The distance from Re to Ga is the same as from Sa to Re (in shuddha/natural form). Ga gives ragas their character — many ragas are defined by how they treat Ga.

**Ma (Madhyam)** — The fourth note. Ma has a particular pull — it wants to resolve upward to Pa or downward to Ga. In shuddha form, it is the natural fourth. (There is also a tivra/sharp Ma used in ragas like Yaman, which we will learn later.)

**Pa (Pancham)** — The fifth, and along with Sa, it is **fixed** — Pa is never altered in any raga. Pa is the second pillar of the tanpura drone. When you sing Pa, you should feel the same stability as Sa, but higher.

**Dha (Dhaivat)** — The sixth note. Dha is to Pa what Re is to Sa — a gentle step above the stable fifth.

**Ni (Nishad)** — The seventh note, just below upper Sa. Ni creates tension — it yearns to resolve upward to Sa'. This pull toward Sa' is one of the most powerful emotional forces in Indian music.

### The Aroha (Ascending) and Avaroha (Descending)

Sing the swaras ascending and descending:

**Aroha:** Sa Re Ga Ma Pa Dha Ni Sa'
**Avaroha:** Sa' Ni Dha Pa Ma Ga Re Sa

This is called singing the **saptak** (the complete octave). Practice this slowly, holding each swara for 2-3 seconds, matching the tanpura drone.

### Common Mistakes to Avoid

1. **Rushing** — spend time on each swara. This is not a race to Sa'.
2. **Ignoring the tanpura** — if you cannot hear the drone, you are singing too loudly.
3. **Flat Ga and Ni** — beginners often sing these slightly flat. Listen carefully.
4. **Tension in the throat** — sing from the belly (diaphragm), not the throat.""",
        "assignments": [
            {
                "title": "Saptak Practice — Ascending and Descending",
                "type": "practice",
                "description": (
                    "With the tanpura drone on, sing the full saptak ascending (Sa Re Ga Ma Pa Dha Ni Sa') "
                    "and descending (Sa' Ni Dha Pa Ma Ga Re Sa). Hold each swara for 3 seconds. "
                    "Repeat 5 times. Focus on pitch accuracy, not speed."
                ),
                "practice_minutes_target": 20,
                "instructions": (
                    "Minutes 1-5: Sing Sa and Pa only, alternating. Lock in these two anchor notes.\n"
                    "Minutes 6-10: Add Re and Dha. Sing Sa-Re-Pa-Dha, back and forth.\n"
                    "Minutes 11-15: Full ascending saptak, very slowly.\n"
                    "Minutes 16-20: Full descending saptak, very slowly.\n"
                    "Tip: Record yourself and listen back. Are the intervals even?"
                ),
            },
            {
                "title": "Swara Recognition — Ear Training",
                "type": "ear_training",
                "description": (
                    "Have someone (or a recording) play individual swaras on a harmonium or keyboard "
                    "with the tanpura drone. Try to identify which swara is being played. "
                    "Start with just Sa, Pa, and Sa' (the easiest). Add Re, Ga, Ma, Dha, Ni gradually."
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
    {
        "title": "Sargam Practice — Melodic Patterns",
        "order": 3,
        "description": "Systematic sargam exercises to build vocal agility, pitch accuracy, and familiarity with swara intervals.",
        "estimated_duration_minutes": 45,
        "topics": ["sargam", "paltas", "vocal exercises", "pitch accuracy"],
        "content": """## Sargam: The Foundation of Practice

Sargam is the practice of singing swara names (Sa, Re, Ga...) in specific melodic patterns. It is the equivalent of scales and exercises in Western music, but with a crucial difference: in Hindustani music, sargam is not just a warm-up — it is the core of your daily practice (riyaaz) throughout your entire musical life.

### Basic Sargam Patterns

Practice each pattern ascending and descending with the tanpura drone:

**Pattern 1 — Straight saptak (revision)**
```
Aroha:   Sa Re Ga Ma Pa Dha Ni Sa'
Avaroha: Sa' Ni Dha Pa Ma Ga Re Sa
```

**Pattern 2 — In pairs (two at a time)**
```
Sa Re - Re Ga - Ga Ma - Ma Pa - Pa Dha - Dha Ni - Ni Sa'
Sa' Ni - Ni Dha - Dha Pa - Pa Ma - Ma Ga - Ga Re - Re Sa
```

**Pattern 3 — In threes (overlapping groups)**
```
Sa Re Ga - Re Ga Ma - Ga Ma Pa - Ma Pa Dha - Pa Dha Ni - Dha Ni Sa'
Sa' Ni Dha - Ni Dha Pa - Dha Pa Ma - Pa Ma Ga - Ma Ga Re - Ga Re Sa
```

**Pattern 4 — Skip one (alternate swaras)**
```
Sa Ga Pa Ni Sa' (ascending, skipping one)
Sa' Dha Ma Re Sa (descending, skipping one)
```

**Pattern 5 — Zigzag**
```
Sa Re Sa - Re Ga Re - Ga Ma Ga - Ma Pa Ma - Pa Dha Pa - Dha Ni Dha - Ni Sa' Ni
```

### How to Practice Sargam

1. **Start slowly** — speed comes naturally with accuracy. If you rush, you will develop bad pitch habits.
2. **One pattern per day** — don't try all five in one sitting. Master one before moving to the next.
3. **Match the drone** — pause on each swara long enough to verify it matches the tanpura.
4. **Use a metronome** — start at 60 BPM (one swara per beat). This builds rhythmic discipline early.
5. **Practice in all three octaves** once comfortable — mandra (lower), madhya (middle), taar (upper).

### The Role of Riyaaz (Daily Practice)

In the Hindustani tradition, riyaaz is sacred. The great vocalist Kishori Amonkar practiced sargam for 3-4 hours daily even at the peak of her career. You do not need that level of commitment as a beginner, but 20 minutes of focused sargam daily will transform your voice within weeks.

The goal of sargam is not mechanical repetition — it is **internalizing the intervals** so deeply that your voice finds the correct swara without conscious effort. This is called **sur lagna** (being in tune), and it is the most important skill in Indian classical music.""",
        "assignments": [
            {
                "title": "Daily Sargam Riyaaz — Week 3",
                "type": "technique",
                "description": (
                    "Practice Patterns 1-3 daily with the tanpura. Start at 60 BPM. "
                    "Each pattern should be sung ascending and descending, 3 times each."
                ),
                "practice_minutes_target": 20,
                "tempo_bpm": 60,
                "instructions": (
                    "Minutes 1-5: Pattern 1 (straight saptak) x3 ascending and descending.\n"
                    "Minutes 6-12: Pattern 2 (pairs) x3 ascending and descending.\n"
                    "Minutes 13-20: Pattern 3 (threes) x3 ascending and descending.\n"
                    "If any pattern feels shaky, spend extra time on it rather than moving forward."
                ),
            },
            {
                "title": "Record and Self-Assess",
                "type": "performance",
                "description": (
                    "Record yourself singing Pattern 3 (threes) ascending and descending. "
                    "Listen back critically: Are the intervals even? Do you rush through any swaras? "
                    "Is your voice steady or wavering? Note one specific area to improve."
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
    {
        "title": "Alankars — Ornamental Patterns",
        "order": 4,
        "description": "Introduction to alankars — systematic melodic ornamentations that develop vocal flexibility and expressiveness.",
        "estimated_duration_minutes": 45,
        "topics": ["alankar", "meend", "kan", "murki", "ornamentation"],
        "content": """## Alankars: The Art of Musical Decoration

Alankars (ornamentations) are melodic patterns that go beyond simple sargam. They are the exercises that develop the grace notes, slides, and turns that make Hindustani music expressive and beautiful. While sargam gives you the skeleton, alankars give you the flesh.

### 10 Essential Beginner Alankars

**Alankar 1 — Four-note ascending groups**
```
Sa Re Ga Ma | Re Ga Ma Pa | Ga Ma Pa Dha | Ma Pa Dha Ni | Pa Dha Ni Sa'
Sa' Ni Dha Pa | Ni Dha Pa Ma | Dha Pa Ma Ga | Pa Ma Ga Re | Ma Ga Re Sa
```

**Alankar 2 — Step up, step back**
```
Sa Re Sa | Re Ga Re | Ga Ma Ga | Ma Pa Ma | Pa Dha Pa | Dha Ni Dha | Ni Sa' Ni
```

**Alankar 3 — Wide leaps**
```
Sa Ma | Re Pa | Ga Dha | Ma Ni | Pa Sa'
Sa' Pa | Ni Ma | Dha Ga | Pa Re | Ma Sa
```

**Alankar 4 — Five-note groups**
```
Sa Re Ga Ma Pa | Re Ga Ma Pa Dha | Ga Ma Pa Dha Ni | Ma Pa Dha Ni Sa'
```

**Alankar 5 — Reverse five-note groups**
```
Pa Ma Ga Re Sa | Dha Pa Ma Ga Re | Ni Dha Pa Ma Ga | Sa' Ni Dha Pa Ma
```

### Introduction to Ornamental Techniques

Beyond the patterns above, Hindustani music uses specific ornamental techniques:

**Meend (glide/slide):** A smooth, continuous slide from one swara to another. This is perhaps the most characteristic technique in Hindustani vocal music. To practice: sing Sa, then slowly slide your voice up to Re without any break in the sound. The slide itself is the beauty.

**Kan swara (grace note):** A fleeting touch of an adjacent note before landing on the target swara. For example, touching Re briefly before landing on Ga. It is barely audible but adds enormous beauty.

**Murki (turn):** A rapid, ornamental cluster of 3-4 notes sung in quick succession. For example, a quick Ga-Ma-Ga before settling on Ga. Murkis give the music a sparkling quality.

**Gamak (oscillation):** A forceful, heavy oscillation between two adjacent swaras. Common in dhrupad and some khayal styles. This is an advanced technique — we will return to it later.

### Practice Notes

- Practice each alankar **very slowly** at first — speed will come with familiarity
- Focus on making each swara clear and distinct, even in fast passages
- Meend practice: spend 5 minutes daily just sliding between Sa-Re, Re-Ga, etc.
- Do not attempt murkis until your basic swaras are perfectly in tune""",
        "assignments": [
            {
                "title": "Alankar Practice — Patterns 1-5",
                "type": "technique",
                "description": (
                    "Practice Alankars 1-5 with the tanpura at 60 BPM. Focus on clarity of each swara "
                    "within the pattern. Ascending and descending, 3 times each."
                ),
                "practice_minutes_target": 25,
                "tempo_bpm": 60,
                "instructions": (
                    "Minutes 1-5: Alankar 1 (four-note groups), slow and steady.\n"
                    "Minutes 6-10: Alankar 2 (step up, step back).\n"
                    "Minutes 11-15: Alankar 3 (wide leaps) — this one is challenging.\n"
                    "Minutes 16-20: Alankars 4-5 (five-note groups).\n"
                    "Minutes 21-25: Meend practice — slide between each adjacent pair of swaras."
                ),
            },
            {
                "title": "Meend Ear Training",
                "type": "ear_training",
                "description": (
                    "Listen to a recording of Pandit Jasraj or Rashid Khan singing khayal. "
                    "Focus specifically on the meend (slides) between notes. Count how many meends "
                    "you can identify in a 5-minute segment. Notice how the slide is never random — "
                    "it always connects specific swaras with intention."
                ),
                "practice_minutes_target": 20,
            },
        ],
    },
    {
        "title": "Introduction to Tala — Rhythm Cycles",
        "order": 5,
        "description": "Understanding the tala system, learning Teen Taal (16 beats), and practicing timekeeping with hand gestures.",
        "estimated_duration_minutes": 45,
        "topics": ["tala", "teen taal", "sam", "khali", "vibhaag", "theka"],
        "content": """## Tala: The Rhythmic Framework

If raga is the soul of Hindustani music, tala is its heartbeat. A tala is a repeating cycle of beats (matras) organized into groups (vibhaags), with a specific pattern of claps (taali) and waves (khali).

### Teen Taal — The Most Common Tala

Teen Taal has **16 beats** (matras) divided into **4 vibhaags** of 4 beats each:

```
Vibhaag 1:  |  1   2   3   4  |  ← Taali (clap) — this is SAM
Vibhaag 2:  |  5   6   7   8  |  ← Taali (clap)
Vibhaag 3:  |  9  10  11  12  |  ← Khali (wave) — open hand wave
Vibhaag 4:  | 13  14  15  16  |  ← Taali (clap)
```

### Key Concepts

**Sam (beat 1):** The most important beat in any tala. The sam is where the cycle restarts, where the singer lands their melodic phrase, where the tabla player's composition resolves. In performance, the vocalist and accompanists make eye contact on sam — it is the moment of musical unity.

**Khali (beat 9 in Teen Taal):** The "empty" beat, marked by an open-palm wave instead of a clap. Khali provides contrast and helps you keep track of where you are in the cycle.

**Theka (basic pattern):** The tabla's default rhythm for a tala. For Teen Taal:
```
Dha  Dhin  Dhin  Dha  |  Dha  Dhin  Dhin  Dha  |  Dha  Tin   Tin   Ta   |  Ta   Dhin  Dhin  Dha
1    2     3     4    |  5    6     7     8    |  9    10    11    12   |  13   14    15    16
```
Notice: beats 9-12 use 'Tin' and 'Ta' (open sounds without bass) — this is the khali section.

### Practicing Tala

**Step 1 — Count and clap:**
Clap on beats 1, 5, 13 (taali). Wave on beat 9 (khali). Count all 16 beats aloud.

**Step 2 — Speak the theka:**
Say the tabla bols (Dha Dhin Dhin Dha...) while clapping/waving. This internalizes the rhythmic feel.

**Step 3 — Sing sargam in tala:**
Sing your sargam patterns (from previous lessons) while keeping Teen Taal with your hands. One swara per beat at first.

### Other Common Talas (Preview)

| Tala | Beats | Vibhaags | Used In |
|------|-------|----------|---------|
| **Teen Taal** | 16 | 4-4-4-4 | Most khayal, instrumental |
| **Ek Taal** | 12 | 2-2-2-2-2-2 | Slow khayal (vilambit) |
| **Rupak** | 7 | 3-2-2 | Light classical |
| **Jhap Taal** | 10 | 2-3-2-3 | Medium tempo khayal |
| **Keherwa** | 8 | 4-4 | Light music, folk |

We will focus on Teen Taal for now. The others will come naturally as you advance.""",
        "assignments": [
            {
                "title": "Teen Taal Clapping Practice",
                "type": "practice",
                "description": (
                    "Practice keeping Teen Taal (16 beats) with hand claps and waves. "
                    "Clap on beats 1, 5, 13. Wave on beat 9. Count all 16 beats aloud. "
                    "Repeat for 10 cycles without losing count."
                ),
                "practice_minutes_target": 15,
                "instructions": (
                    "Minutes 1-5: Count and clap Teen Taal slowly. Say the beat numbers aloud.\n"
                    "Minutes 6-10: Speak the theka (Dha Dhin Dhin Dha...) while clapping.\n"
                    "Minutes 11-15: Sing Sa-Re-Ga-Ma (one per beat) while keeping tala with hands.\n"
                    "Goal: Complete 10 consecutive cycles without losing your place."
                ),
            },
            {
                "title": "Tala Listening — Identify Sam",
                "type": "ear_training",
                "description": (
                    "Listen to a Teen Taal tabla solo or accompaniment (search 'Teen Taal tabla theka' on YouTube). "
                    "Try to identify beat 1 (sam) each time the cycle restarts. "
                    "Clap along. Notice the characteristic 'Dha' sound on sam."
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
    {
        "title": "Raga Yaman — Your First Raga",
        "order": 6,
        "description": "Introduction to Raga Yaman — the traditional first raga taught to beginners. Learning its swaras, aroha/avaroha, and characteristic phrases.",
        "estimated_duration_minutes": 50,
        "topics": ["Raga Yaman", "tivra Ma", "aroha", "avaroha", "pakad", "chalan"],
        "content": """## Raga Yaman: The Jewel of Evening

Raga Yaman (also called Kalyan) is traditionally the first raga taught to students in Hindustani music. It is an evening raga, meant to be sung between sunset and midnight, and it evokes feelings of devotion, romance, and quiet grandeur.

### Why Yaman First?

- All swaras are shuddha (natural) except **tivra Ma** (sharp fourth) — only one altered note
- The intervals are symmetrical and pleasing to the ear
- It is one of the most widely performed ragas, so listening material is abundant
- Its mood is gentle and uplifting — ideal for developing musical confidence

### The Swaras of Raga Yaman

Yaman uses all seven swaras with **tivra Ma** (written as Ma' or M'):

**Sa Re Ga Ma'(tivra) Pa Dha Ni**

Tivra Ma is raised by a half-step compared to shuddha Ma. If you have been singing Sa Re Ga Ma Pa..., the Ma in Yaman is slightly higher than what you have practiced. This is a crucial distinction — the tivra Ma gives Yaman its characteristic bright, upward-reaching quality.

### Aroha and Avaroha

Yaman's aroha (ascent) and avaroha (descent) are not straight scales. This is your first lesson in a critical principle: **ragas are not scales**.

```
Aroha:    Ni Re Ga Ma' Pa Dha Ni Sa'
          (Note: starts from Ni of the lower octave, skips Sa)

Avaroha:  Sa' Ni Dha Pa Ma' Ga Re Sa
          (Straight descent)
```

The ascending pattern **skips Sa** and starts from the lower Ni. This is a defining rule of Yaman — in the ascent, you approach Sa from below (via Ni) rather than starting on it directly. This gives the raga its characteristic sense of aspiration.

### Pakad — The Identity Phrase

Every raga has a **pakad** (catch phrase) — a short melodic fragment that instantly identifies it. For Yaman:

```
Ni Re Ga, Ma' Pa, Dha Ni Sa'
```

If someone sings these notes in this pattern, any listener familiar with Hindustani music will immediately recognize Yaman.

### Characteristic Phrases (Chalan)

Practice these phrases to internalize Yaman's grammar:

```
Phrase 1: Ni Re Ga Re Sa  (approach from below)
Phrase 2: Ga Ma' Pa       (the bright ascent through tivra Ma)
Phrase 3: Pa Dha Ni Sa'   (upper reach)
Phrase 4: Sa' Ni Dha Pa Ma' Ga Re Sa  (full descent)
Phrase 5: Ni Dha Pa Ma' Ga Re Sa      (long descent from upper octave)
```

### Important Rules

1. **Never sing Sa directly in ascent** — always approach through Ni-Re or Ni-Sa-Re
2. **Tivra Ma only** — never use shuddha Ma in Yaman
3. **Ga is the heart** — many phrases rest on or revolve around Ga
4. **Evening raga** — traditionally sung after sunset

### Mood and Rasa

Yaman evokes **shringaar rasa** (romantic sentiment) and **bhakti** (devotion). When you sing Yaman, imagine a quiet evening, perhaps oil lamps being lit, a sense of gentle longing. Let this mood guide your musical choices.""",
        "assignments": [
            {
                "title": "Raga Yaman — Aroha/Avaroha Practice",
                "type": "practice",
                "description": (
                    "Sing the aroha (Ni Re Ga Ma' Pa Dha Ni Sa') and avaroha "
                    "(Sa' Ni Dha Pa Ma' Ga Re Sa) of Raga Yaman with the tanpura. "
                    "Pay special attention to the tivra Ma — it should sound distinctly "
                    "higher than the shuddha Ma you practiced earlier."
                ),
                "practice_minutes_target": 20,
                "instructions": (
                    "Minutes 1-5: Sing the aroha slowly, 5 times. Notice how Sa is skipped.\n"
                    "Minutes 6-10: Sing the avaroha slowly, 5 times.\n"
                    "Minutes 11-15: Alternate aroha and avaroha continuously.\n"
                    "Minutes 16-20: Practice the 5 characteristic phrases listed in the lesson."
                ),
            },
            {
                "title": "Yaman Listening — Three Masters",
                "type": "ear_training",
                "description": (
                    "Listen to three different performances of Raga Yaman by different artists. "
                    "Suggested: Kishori Amonkar, Rashid Khan, and Ajoy Chakraborty. "
                    "Notice how each artist interprets the same raga differently while following "
                    "the same rules. Can you identify the pakad (Ni Re Ga, Ma' Pa) in each performance?"
                ),
                "practice_minutes_target": 30,
            },
        ],
    },
    {
        "title": "Alaap — Slow Raga Exploration",
        "order": 7,
        "description": "The art of alaap — the unaccompanied, meditative introduction to a raga, exploring its mood note by note.",
        "estimated_duration_minutes": 45,
        "topics": ["alaap", "vistar", "raga exploration", "barhat"],
        "content": """## Alaap: Where Music Becomes Meditation

Alaap is the opening section of a Hindustani classical performance. It is sung slowly, without any rhythmic accompaniment (no tabla), accompanied only by the tanpura drone. In alaap, the singer gradually unveils the raga note by note, phrase by phrase, moving from the lower register to the upper.

### The Structure of Alaap

Alaap follows a deliberate progression:

**1. Sthayi (establishing the base)**
Begin with Sa. Introduce Re. Then Ga. Spend time on each swara, exploring its relationship to Sa and to the notes around it. Stay in the lower and middle register.

**2. Barhat (expansion)**
Gradually move upward, introducing Pa, Dha, Ni. Each new swara is approached tentatively — touch it, return to familiar ground, then approach again with more confidence.

**3. Reaching Sa' (the upper tonic)**
The arrival at upper Sa' is a climactic moment. It should feel earned, not rushed.

### Alaap in Raga Yaman — A Step-by-Step Guide

Here is how to build an alaap in Yaman. Sing each line slowly, with pauses between phrases:

```
Step 1 — Establish Sa:
  Sa... Sa... (sustain, feel the drone)

Step 2 — Introduce Ni and Re:
  Ni Sa... Re Sa... Ni Re Sa...

Step 3 — Bring in Ga:
  Ni Re Ga... Ga Re Sa... Ni Re Ga Re Sa...

Step 4 — Introduce tivra Ma:
  Ga Ma' Ga... Re Ga Ma' Pa... (Ma' opens the door to Pa)

Step 5 — Arrive at Pa:
  Ga Ma' Pa... Pa Ma' Ga Re Sa... (descent to ground yourself)

Step 6 — Explore Dha and Ni:
  Pa Dha Pa... Pa Dha Ni Sa'... (approaching the upper Sa')

Step 7 — Reach Sa':
  Dha Ni Sa'... Sa' Ni Dha Pa Ma' Ga Re Sa (full descent home)
```

### The Principles of Good Alaap

1. **Patience** — There is no hurry. A great alaap in Yaman by a master vocalist can last 30 minutes. Yours might be 3 minutes. Both are valid.

2. **Return to Sa** — After each new exploration, return to Sa. This grounds the listener and reinforces the tonic.

3. **Less is more** — A single beautiful phrase repeated with slight variation is more powerful than a flurry of notes.

4. **Breath is music** — The silences between phrases are as important as the notes. Let each phrase breathe.

5. **Emotion first** — You are not demonstrating the rules of Yaman. You are expressing a mood through its framework. Feel the evening, the devotion, the quiet longing.

### Alaap vs. Sargam

In sargam practice, you sing note names (Sa, Re, Ga...). In alaap, you sing **aakaar** — the open vowel sound "aa" (or sometimes "re ne na" syllables). The notes are the same, but the expression is freer, more vocal, more emotional.""",
        "assignments": [
            {
                "title": "Build a 3-Minute Alaap in Yaman",
                "type": "performance",
                "description": (
                    "Following the step-by-step guide in the lesson, build a short alaap in Raga Yaman. "
                    "Start from Sa, gradually introduce each swara, reach Sa', and descend back. "
                    "Record it. It should be 2-3 minutes long. Sing on 'aa' (aakaar), not swara names."
                ),
                "practice_minutes_target": 30,
                "instructions": (
                    "Minutes 1-10: Practice the 7 steps from the lesson, using swara names.\n"
                    "Minutes 11-20: Repeat, but now sing on 'aa' (aakaar) instead of swara names.\n"
                    "Minutes 21-25: Do a continuous alaap from start to finish without stopping.\n"
                    "Minutes 26-30: Record your best attempt. Listen back."
                ),
            },
        ],
    },
    {
        "title": "Bandish in Raga Yaman — Learning a Composition",
        "order": 8,
        "description": "Learning a traditional bandish (composition) in Raga Yaman set to Teen Taal, combining melody and rhythm.",
        "estimated_duration_minutes": 50,
        "topics": ["bandish", "sthayi", "antara", "khayal", "composition"],
        "content": """## Bandish: The Heart of Khayal

A bandish is a fixed composition in a raga, set to a specific tala. It serves as the launchpad for improvisation in the khayal style. Every khayal performance begins with the singer presenting a bandish, then improvising around it.

### Structure of a Bandish

A bandish has two main parts:

**Sthayi (refrain):** The main section, centered in the middle octave (madhya saptak). It always begins on or near Sam (beat 1 of the tala cycle). The sthayi is the part you return to again and again.

**Antara (verse):** The second section, which ascends to the upper octave (taar saptak). It provides contrast and expansion.

### Your First Bandish — "Eri Aali Piya Bina"

This is a traditional bandish in Raga Yaman, set to Teen Taal (16 beats). It is widely taught to beginners.

**Sthayi:**
```
Tala:  |  1    2    3    4  |  5    6    7    8  |  9    10   11   12 |  13   14   15   16 |
Text:  |  E  - ri   aa - li |  pi - ya   bi - na |  na - hi   aa - vat |  chain -  -   -  |
Swara: |  Ni   Re   Ga   Re |  Ga   Ma'  Pa   Ma'|  Ga   Re   Ni   Sa |  Re  -    -    -  |
```
(Meaning: "Oh friend, without my beloved, there is no peace")

**Antara:**
```
Tala:  |  1    2    3    4  |  5    6    7    8  |  9    10   11   12 |  13   14   15   16 |
Text:  |  Ja - ba   se   pi |  ya   pa - ra - des|  ga - ye   -    -  |  tab  -    se   -  |
Swara: |  Pa   Dha  Ni   Sa'|  Sa'  Ni   Dha  Pa |  Ma'  Ga   -    -  |  Re   -    Sa   -  |
```
(Meaning: "Since my beloved went to a distant land...")

### How to Learn the Bandish

**Step 1 — Learn the melody (without tala)**
Sing just the swaras of the sthayi slowly, without worrying about rhythm. Get the notes right first.

**Step 2 — Add the words**
Once the melody is secure, add the Hindi text. The words and notes should flow together naturally.

**Step 3 — Add Teen Taal**
Now sing the sthayi while keeping Teen Taal with your hands. The word "E-ri" should land on Sam (beat 1).

**Step 4 — Loop the sthayi**
Sing the sthayi repeatedly. In a real performance, you would sing it 2-3 times before moving to the antara.

**Step 5 — Learn the antara**
Follow the same process for the antara. The antara's melody reaches into the upper octave.

**Step 6 — Connect sthayi and antara**
The performance order is: Sthayi → Sthayi → Antara → Sthayi (return).

### Understanding the Bandish Musically

Notice how the sthayi stays in the middle register (Ni to Pa), while the antara reaches up to Sa'. This is by design — the sthayi establishes the raga's core, the antara expands the range, and then you return to the familiar sthayi.""",
        "assignments": [
            {
                "title": "Learn the Sthayi of 'Eri Aali'",
                "type": "practice",
                "description": (
                    "Learn the sthayi (first section) of the bandish. First learn the swara melody "
                    "without rhythm, then add the words, then add Teen Taal. Practice until you can "
                    "sing it smoothly 3 times in a row with tala."
                ),
                "practice_minutes_target": 30,
                "instructions": (
                    "Days 1-2: Sing only the swaras (Ni Re Ga Re Ga Ma' Pa Ma'...) slowly.\n"
                    "Days 3-4: Add the Hindi text while maintaining the melody.\n"
                    "Days 5-7: Sing with Teen Taal clapping. Land 'Eri' on Sam (beat 1)."
                ),
            },
            {
                "title": "Theory — Analyze the Bandish",
                "type": "theory",
                "description": (
                    "Write down the swaras used in the sthayi and antara. "
                    "Identify: (1) Which swara does the sthayi start on? "
                    "(2) What is the highest note in the antara? "
                    "(3) Where does tivra Ma appear? "
                    "(4) How does the bandish follow Yaman's aroha/avaroha rules?"
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
    {
        "title": "Raga Bhairav — The Morning Raga",
        "order": 9,
        "description": "Learning Raga Bhairav — a contrasting morning raga with komal swaras, exploring its serious and devotional character.",
        "estimated_duration_minutes": 45,
        "topics": ["Raga Bhairav", "komal swaras", "morning raga", "raga time theory"],
        "content": """## Raga Bhairav: Dawn and Devotion

After the gentle evening beauty of Yaman, we now turn to Raga Bhairav — a morning raga of gravity, devotion, and solemnity. Where Yaman is bright and romantic, Bhairav is deep and meditative. Named after Lord Shiva in his fierce form, this raga carries the weight of dawn itself.

### Raga Time Theory

In Hindustani music, ragas are traditionally assigned to specific times of day. This is not arbitrary — it reflects the belief that certain intervals resonate with the mood and energy of different hours:

- **Sunrise ragas** (Bhairav, Todi) — use komal (flat) Re and Dha
- **Morning ragas** (Asavari, Darbari) — komal Ga, Dha, Ni
- **Afternoon ragas** (Bhimpalasi, Multani) — bridge between morning and evening
- **Evening/night ragas** (Yaman, Kalyan) — tivra Ma, shuddha Re and Ga

### The Swaras of Raga Bhairav

Bhairav uses two **komal** (flat) swaras — Re and Dha:

**Sa re(komal) Ga Ma Pa dha(komal) Ni Sa'**

The komal Re and komal Dha give Bhairav its characteristic gravity. These flattened notes create narrow intervals (Sa to komal Re is just a semitone) that produce a sense of tension and depth.

### Aroha and Avaroha

```
Aroha:   Sa re Ga Ma Pa dha Ni Sa'
Avaroha: Sa' Ni dha Pa Ma Ga re Sa
```

Unlike Yaman, Bhairav's ascent and descent are relatively straight. However, the emphasis and treatment of swaras is where the raga's character lives.

### Pakad (Identity Phrase)

```
re Sa, Ga Ma re Sa, dha Pa, Ni dha Pa Ma Ga re Sa
```

Notice the characteristic descent through komal Re to Sa — this is Bhairav's signature sound, a heavy, gravitational pull downward.

### Characteristic Phrases

```
Phrase 1: Sa re Sa          (the tight Sa-re oscillation — quintessential Bhairav)
Phrase 2: Ga Ma re Sa       (descent through komal Re)
Phrase 3: Ma Pa dha Pa      (the komal Dha gives gravity to the upper register)
Phrase 4: Ni dha Pa Ma Ga   (long, majestic descent)
Phrase 5: re Ga Ma Pa       (ascent through the komal Re — note the tension)
```

### Comparing Yaman and Bhairav

| Aspect | Yaman | Bhairav |
|--------|-------|---------|
| Time | Evening | Morning |
| Altered swaras | Tivra Ma (one sharp) | Komal Re and Dha (two flats) |
| Mood | Romantic, bright | Devotional, grave |
| Feeling | Aspiration, yearning | Solemnity, grandeur |
| Sa treatment | Approached from below (Ni) | Approached from above (re) |

### The Emotional World of Bhairav

When you sing Bhairav, imagine the very first light of dawn — before the sun is visible, when the world is still and grey. There is something both awe-inspiring and solemn about this hour. Bhairav captures exactly this feeling.""",
        "assignments": [
            {
                "title": "Raga Bhairav — Aroha/Avaroha and Phrases",
                "type": "practice",
                "description": (
                    "Sing the aroha and avaroha of Raga Bhairav with the tanpura. "
                    "Pay careful attention to komal Re (very close to Sa) and komal Dha (very close to Pa). "
                    "Then practice the 5 characteristic phrases."
                ),
                "practice_minutes_target": 25,
                "instructions": (
                    "Minutes 1-5: Sing just Sa and komal Re, back and forth. Feel the narrow interval.\n"
                    "Minutes 6-10: Full aroha and avaroha, slowly.\n"
                    "Minutes 11-20: Practice the 5 characteristic phrases.\n"
                    "Minutes 21-25: Try a short alaap in Bhairav (use the same method as Yaman alaap)."
                ),
            },
            {
                "title": "Compare Yaman and Bhairav by Ear",
                "type": "ear_training",
                "description": (
                    "Listen to one performance of Yaman and one of Bhairav back to back. "
                    "Write down 3 specific musical differences you can hear. "
                    "Can you feel the time-of-day association? Which feels like morning, which like evening?"
                ),
                "practice_minutes_target": 20,
            },
        ],
    },
    {
        "title": "Taan — Fast Melodic Passages",
        "order": 10,
        "description": "Introduction to taan — rapid melodic runs that showcase vocal agility and mastery of the raga's swaras.",
        "estimated_duration_minutes": 45,
        "topics": ["taan", "sapat taan", "vakra taan", "speed", "vocal agility"],
        "content": """## Taan: Speed with Precision

Taan refers to rapid melodic passages sung in a raga performance. If alaap is the meditative, slow exploration of a raga, taan is its exhilarating, fast counterpart. Taans demonstrate the vocalist's command over the raga, their vocal agility, and their ability to maintain pitch accuracy at high speed.

### Types of Taan

**Sapat Taan (straight runs):**
Fast ascending and descending runs through the swaras in order.
```
Sa Re Ga Ma Pa Dha Ni Sa' (very fast)
Sa' Ni Dha Pa Ma Ga Re Sa (very fast)
```

**Vakra Taan (zigzag/curved runs):**
Fast patterns with twists and turns.
```
Sa Re Ga Re Ga Ma Ga Ma Pa Ma Pa Dha Pa Dha Ni Dha Ni Sa'
```

**Alankar-based Taan:**
Fast execution of alankar patterns you already know.
```
Sa Re Ga Ma | Re Ga Ma Pa | Ga Ma Pa Dha | Ma Pa Dha Ni  (fast)
```

### Building Speed — The Systematic Approach

Speed in taan is built gradually. **Never start fast.** The progression:

**1. Foundation (60 BPM):** Sing the pattern slowly, ensuring every swara is perfectly in tune.

**2. Medium (90 BPM):** Increase speed slightly. At this tempo, you might start losing clarity on certain swaras — identify which ones and practice them.

**3. Fast (120 BPM):** At this speed, the pattern should feel flowing, not choppy. Each swara should still be distinct.

**4. Performance tempo (150+ BPM):** This takes months to years of practice. Do not rush to get here.

### Taan Practice in Raga Yaman

Since Yaman is your primary raga, practice taans within its framework:

```
Taan 1 (sapat): Ni Re Ga Ma' Pa Dha Ni Sa' Sa' Ni Dha Pa Ma' Ga Re Sa
Taan 2 (vakra): Ni Re Ga Re Ga Ma' Ga Ma' Pa Ma' Pa Dha Pa Dha Ni Dha Ni Sa'
Taan 3 (pattern): Ni Re Ga Ma' | Re Ga Ma' Pa | Ga Ma' Pa Dha | Ma' Pa Dha Ni
```

Remember: these use tivra Ma', following Yaman's rules.

### Common Taan Mistakes

1. **Sacrificing pitch for speed** — if you go sharp or flat at speed, slow down. Pitch always comes first.
2. **Swallowing swaras** — every note in the taan must be audible, even at high speed.
3. **Rhythmic irregularity** — taans should be evenly spaced. Use a metronome.
4. **Forcing the throat** — taans come from breath support and diaphragm control, not throat tension.

### Breath Management for Taans

A taan requires a full, controlled breath. Before beginning a long taan:
- Take a deep breath from the diaphragm
- Start the taan on the exhale
- Plan your phrase to end where you can naturally breathe
- In performance, vocalists often take a quick breath at a musically natural point and continue""",
        "assignments": [
            {
                "title": "Speed Building — Sapat Taan in Yaman",
                "type": "technique",
                "description": (
                    "Practice Taan 1 (sapat/straight) in Raga Yaman at three speeds: "
                    "60 BPM, 80 BPM, and 100 BPM. Spend 5 minutes at each speed. "
                    "Only move to the next speed when the current one is clean."
                ),
                "practice_minutes_target": 20,
                "tempo_bpm": 60,
                "instructions": (
                    "Minutes 1-7: 60 BPM — focus on pitch accuracy.\n"
                    "Minutes 8-14: 80 BPM — maintain clarity.\n"
                    "Minutes 15-20: 100 BPM — if this feels sloppy, return to 80.\n"
                    "Record your 100 BPM attempt and listen for any swaras that are unclear."
                ),
            },
        ],
    },
    {
        "title": "Raga Bhimpalasi — The Afternoon Raga",
        "order": 11,
        "description": "Learning Raga Bhimpalasi — a beautiful afternoon raga with komal Ga and Ni, known for its gentle, yearning quality.",
        "estimated_duration_minutes": 45,
        "topics": [
            "Raga Bhimpalasi",
            "komal Ga",
            "komal Ni",
            "afternoon raga",
            "vakra movement",
        ],
        "content": """## Raga Bhimpalasi: The Gentle Afternoon

Raga Bhimpalasi is an afternoon raga (3 PM to 6 PM) of immense beauty and accessibility. It is one of the most beloved ragas in the Hindustani repertoire, known for its gentle, yearning quality. Where Yaman soars and Bhairav broods, Bhimpalasi tenderly aches.

### The Swaras of Bhimpalasi

Bhimpalasi uses two komal (flat) swaras — Ga and Ni:

**Sa Re ga(komal) Ma Pa Dha ni(komal) Sa'**

However, Re and Dha are **vakra** (used in a zigzag fashion) — they appear in descent but are often skipped in ascent. This gives Bhimpalasi its distinctive winding movement.

### Aroha and Avaroha

```
Aroha:   Sa ga Ma Pa, ni Dha Pa (vakra — not a straight ascent)
         or simply: Sa ga Ma Pa ni Sa'

Avaroha: Sa' ni Dha Pa, Ma Pa Dha Pa Ma ga Re Sa
```

Notice: the ascent skips Re and Dha, while the descent includes them. The phrase "Ma Pa Dha Pa" in the descent is one of Bhimpalasi's most characteristic movements.

### Pakad (Identity Phrase)

```
Ma Pa, ga Ma ga Re Sa
ni Dha Pa, Ma Pa Dha Pa Ma ga Re Sa
```

The oscillation around Ma and Pa is the heart of Bhimpalasi. The raga lives in the relationship between these two swaras.

### Characteristic Phrases

```
Phrase 1: Sa ga Ma Pa         (basic ascent — komal Ga rises to Ma)
Phrase 2: Ma Pa Dha Pa Ma     (the signature turn around Pa)
Phrase 3: ga Ma ga Re Sa      (descent through the lower register)
Phrase 4: ni Dha Pa Ma Pa     (upper register exploration)
Phrase 5: Pa Ma ga Re Sa      (final descent to rest)
```

### The Emotional World of Bhimpalasi

Bhimpalasi evokes **viraha** (the pain of separation) and gentle longing. It is the perfect 'thinking of someone' raga — not dramatic grief, but the quiet ache of missing someone on a warm afternoon. Many of the most beautiful thumris and ghazals are set in Bhimpalasi.

### Three Ragas Compared

| Aspect | Yaman | Bhairav | Bhimpalasi |
|--------|-------|---------|------------|
| Time | Evening | Morning | Afternoon |
| Altered swaras | Tivra Ma | Komal Re, Dha | Komal Ga, Ni |
| Movement | Straight | Straight | Vakra (zigzag) |
| Mood | Romance, devotion | Solemnity, awe | Yearning, tenderness |
| Dominant swara | Ga | re | Ma/Pa |

You now know three ragas from three different times of day, each with a distinct emotional palette. This is how Hindustani music maps the human experience onto the hours of the day.""",
        "assignments": [
            {
                "title": "Raga Bhimpalasi — Phrases and Short Alaap",
                "type": "practice",
                "description": (
                    "Learn the aroha/avaroha and 5 characteristic phrases of Bhimpalasi. "
                    "Then attempt a short 2-minute alaap, following the same structure you used for Yaman. "
                    "Pay attention to the vakra (zigzag) movement."
                ),
                "practice_minutes_target": 25,
                "instructions": (
                    "Minutes 1-5: Aroha and avaroha, slowly, with tanpura.\n"
                    "Minutes 6-15: Practice each of the 5 characteristic phrases.\n"
                    "Minutes 16-25: Build a short alaap — start with Sa, introduce ga, Ma, Pa, "
                    "then explore the upper register. Remember: this raga loves to hover around Ma-Pa."
                ),
            },
            {
                "title": "Raga Identification — Yaman, Bhairav, or Bhimpalasi?",
                "type": "ear_training",
                "description": (
                    "Ask a friend or teacher to sing or play short phrases from Yaman, Bhairav, "
                    "or Bhimpalasi (randomly). Try to identify which raga each phrase belongs to. "
                    "Alternatively, shuffle recordings of all three and identify by ear."
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
    {
        "title": "Performance Preparation — Putting It All Together",
        "order": 12,
        "description": "Combining alaap, bandish, taan, and raga exploration into a complete mini-performance in Raga Yaman.",
        "estimated_duration_minutes": 50,
        "topics": ["performance", "presentation", "improvisation", "concert format"],
        "content": """## Your First Complete Performance

Over the past 11 weeks, you have learned swaras, alankars, tala, three ragas, alaap, bandish, and taan. Now it is time to put it all together into a complete mini-performance in Raga Yaman.

### The Structure of a Khayal Performance

A traditional khayal performance follows this structure:

```
1. Alaap (2-5 min)     — slow, unmetered raga exploration
2. Bandish presentation — sing the sthayi 2-3 times
3. Vistar/Barhat        — improvise around the sthayi, expanding the raga
4. Antara               — sing the antara, reaching the upper octave
5. Taan section         — fast melodic passages
6. Return to Sthayi     — come home to the refrain
```

### Building Your 5-Minute Performance

**Section 1: Alaap (1-2 minutes)**
Begin with the alaap you practiced in Week 7. Start from Sa, gradually introduce Ni, Re, Ga, tivra Ma, Pa. Reach Sa' and descend. Sing on 'aa' (aakaar). No tala — this is free and meditative.

**Section 2: Enter the Bandish (1 minute)**
After the alaap, begin keeping Teen Taal with your hands. Sing the sthayi of "Eri Aali Piya Bina" twice. Let the rhythm establish itself.

**Section 3: Simple Vistar (1 minute)**
Between repetitions of the sthayi, insert a short improvisatory phrase. For example, after singing the sthayi once, sing a phrase like "Ni Re Ga Ma' Pa... Ga Re Sa" and then return to the sthayi. This is the beginning of improvisation.

**Section 4: Antara (30 seconds)**
Sing the antara once. Feel the expansion into the upper octave.

**Section 5: One Taan + Return (30 seconds)**
Sing one clean sapat taan ascending and descending. Then return to the sthayi to close the performance.

### Performance Tips

1. **Start slow, end fast** — this is the natural arc of a Hindustani performance.
2. **Always return to the sthayi** — it is your anchor, your home. The audience expects it.
3. **Mistakes are fine** — in Indian classical music, a skilled musician turns mistakes into opportunities. If you land on a wrong swara, slide gracefully to the correct one.
4. **Connect with the raga's mood** — close your eyes, feel the evening, let Yaman speak through you.
5. **End on Sam** — your final phrase should resolve on beat 1 of Teen Taal.

### What You Have Achieved

In 12 weeks, you have:
- Learned the swara system and can sing in tune with a drone
- Mastered basic alankars and sargam patterns
- Learned to keep Teen Taal (16 beats)
- Explored three ragas — Yaman, Bhairav, and Bhimpalasi
- Performed alaap, bandish, and taan
- Developed the ear to distinguish ragas

### Where to Go Next

- **Intermediate course:** More ragas (Todi, Marwa, Darbari), thumri style, more complex talas
- **Advanced course:** Layakari (rhythmic play), extensive improvisaiton, khayal gayaki (singing style)
- **Daily riyaaz:** Continue 30 minutes of sargam + 30 minutes of raga practice daily
- **Listen voraciously:** The more you listen, the more your musical vocabulary grows

Congratulations — you are now a Hindustani classical vocalist. The journey of a thousand ragas begins with a single Sa.""",
        "assignments": [
            {
                "title": "Record Your Complete Performance",
                "type": "performance",
                "description": (
                    "Record a 5-minute mini-performance in Raga Yaman following the structure "
                    "outlined in this lesson: Alaap → Bandish (sthayi) → Short vistar → Antara → "
                    "Taan → Return to sthayi. Use a tanpura app for the drone."
                ),
                "practice_minutes_target": 45,
                "instructions": (
                    "Days 1-3: Practice each section separately.\n"
                    "Days 4-5: Do full run-throughs, noting where transitions feel awkward.\n"
                    "Days 6-7: Record 2-3 takes. Pick your best one.\n"
                    "Listen to your recording with fresh ears the next day. "
                    "Note what you are proud of and what you want to improve."
                ),
            },
            {
                "title": "Self-Assessment and Goal Setting",
                "type": "theory",
                "description": (
                    "Write a brief self-assessment: (1) Which raga do you feel most confident in? "
                    "(2) Is your pitch accuracy better in slow alaap or fast taan? "
                    "(3) Can you keep Teen Taal steady for 5 cycles without losing count? "
                    "(4) What do you want to learn next? "
                    "Share this with your instructor for personalized feedback."
                ),
                "practice_minutes_target": 15,
            },
        ],
    },
]
