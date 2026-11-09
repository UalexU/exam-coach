# exam.json schema

`scripts/build_exam.py` reads this file and renders the interactive page, the printable paper and the answer key from it. Write the JSON first, run `--check`, fix what it reports, then build.

Text fields accept a tiny, safe markdown: `` `code` ``, `**bold**`, `*italic*`, `x^{2}` (superscript), `μ_{0}` (subscript), and line breaks. HTML is escaped, so don't use it.

```jsonc
{
  "meta": {
    "series": "Electromagnetism Exam Series", // same string every time, used to find earlier exams
    "number": 4,                               // position in the series
    "title": "Exam 4: Magnetic circuits and saturation",
    "date": "2026-11-09",
    "field": "Electromagnetism",
    "level": "Undergraduate",
    "professor": {
      "name": "Prof. Ada Lindqvist (persona)",
      "persona": "Experimental physicist who builds electromagnets; Socratic; strict on units and assumptions"
    },
    "topics": ["Solenoid field", "Magnetic circuits", "Core saturation"],
    "time_limit_minutes": 45,                  // null = untimed
    "instructions": "Answer all questions. Show units. State assumptions."
  },
  "questions": [
    {
      "id": "q1",                              // letters, digits, - or _; unique
      "type": "mc",                            // "mc" | "short" | "long"
      "concept": "Solenoid field",             // REQUIRED: stable name, drives history and review
      "objective": "U1.1",                     // REQUIRED when a syllabus is used: syllabus objective id
      "objective_text": "Compute the field inside a solenoid…", // optional, shown in results
      "kind": "new",                           // review | new | transfer | pretest
      "bloom": "apply",                        // remember | understand | apply | analyze | evaluate | create
      "difficulty": 3,                         // 1-5, aim for an average of 3-4
      "hint": "Turns per meter first. What number does μ_{0} carry?", // optional Socratic nudge
      "points": 1,
      "prompt": "A 20 cm solenoid has 400 turns and carries 2.0 A. What is the field near its center?",
      "options": [
        {"id": "A", "text": "5.0 mT"},
        {"id": "B", "text": "50 mT"},
        {"id": "C", "text": "1.6 mT"},
        {"id": "D", "text": "2.5 mT"}
      ],
      "answer": "A",
      "explanation": "B = μ_{0}nI = (4π × 10^{-7})(2000 m^{-1})(2.0 A) ≈ 5.0 mT.",
      "distractor_notes": {                    // why each wrong option is tempting
        "B": "Off by 10×: took 20 cm as 0.02 m.",
        "C": "Dropped the π in μ_{0}.",
        "D": "The field at the end of the solenoid, not the center."
      },
      "sources": [
        {"title": "Ling SJ, Sanny J, Moebs W. University Physics Volume 2. OpenStax; 2016",
         "url": "https://openstax.org/details/books/university-physics-volume-2", "note": "Chapter 12, Solenoids and toroids"}
      ]
    },
    {
      "id": "q2",
      "type": "short",                         // "long" has the same fields
      "concept": "Magnetic circuits",
      "points": 4,
      "expected_length": "4-6 sentences",
      "answer_lines": 12,                      // optional: ruled lines on the printed paper
      "prompt": "Derive the gap field of an iron-core electromagnet and explain why the gap, not the iron, sets it.",
      "rubric": [                              // points MUST add up to the question's points
        {"criterion": "Ampère's law", "points": 2, "description": "NI = H_{i}l_{i} + H_{g}g with B continuous, so B_{g} = μ_{0}NI / (g + l_{i}/μ_{r})."},
        {"criterion": "Large-μ_{r} limit", "points": 2, "description": "When l_{i}/μ_{r} ≪ g, B_{g} ≈ μ_{0}NI / g: the gap holds most of the reluctance."}
      ],
      "model_answer": "…",                     // a strong reference answer
      "alternatives": "A reluctance-network argument is equally valid if the result is correct.",
      "sources": [ {"title": "…", "url": "…"} ]
    }
  ],
  "review_note": "Re-derived all MC keys independently; rewrote q3 because two options were defensible; balanced answer letters."
}
```

## syllabus.json

```jsonc
{
  "course": "Electromagnetism: Fields and Electromagnets (undergraduate)",
  "source": "Syllabus PDF, fall 2026",
  "units": [
    {
      "id": "U2",
      "title": "Electromagnets and magnetic materials",
      "start": "2026-11-02", "end": "2026-11-15",          // ISO dates; derive them from week numbers if needed
      "readings": ["Griffiths, Introduction to Electrodynamics, ch. 6"],
      "objectives": [
        {"id": "U2.1", "text": "Derive the gap field of an iron-core electromagnet",
         "concept": "Magnetic circuits", "importance": "core"},       // core | supporting
        {"id": "U2.4", "text": "Estimate resistive heating in a coil and how it scales with field",
         "concept": "Coil heating", "importance": "supporting"}
      ]
    }
  ]
}
```

Write objectives as observable outcomes (derive, predict, choose and justify), not topics. Use the same `concept` names in exams so history, objectives and results line up.

## Validation rules (`--check`)

Errors (build stops):

- `meta.title` and `meta.field` present; `time_limit_minutes` positive or `null`
- unique, well-formed ids; known `type`; non-empty `prompt`; `points` > 0
- MC: ≥ 3 options with unique ids, `answer` matches an option, `explanation` present
- reasoning: `rubric` present, each row has a `criterion`, rubric points sum to `points`, `model_answer` present
- every source has a `title`
- every question has a `concept`; `difficulty`, if given, is 1-5
- MC: every wrong option has a `distractor_notes` entry (its named flaw)
- with `--syllabus`: every question has an `objective` that exists in the syllabus

Warnings (fix them unless there's a reason not to):

- a question with no sources
- reasoning question with no `alternatives`
- keyed MC option much longer than the rest (give-away cue)
- one answer letter is the key in more than 45% of MC items
- "all/none of the above"
- fewer than 4 MC options
- a `remember`-level item that isn't a pretest; over 25% recall/understand items (excluding pretests)
- mean difficulty below 3
- with `--syllabus`: an objective from a unit that starts after the exam date (unless `pretest`); core objectives of the current unit not tested; under 60% of points on core objectives
- time limit shorter than a rough estimate (1.25 min per MC, 6 per short, 20 per long)
- missing `review_note`
