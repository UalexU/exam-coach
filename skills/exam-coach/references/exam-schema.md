# exam.json schema

`scripts/build_exam.py` reads this file and renders the interactive page, the printable paper and the answer key from it. Write the JSON first, run `--check`, fix what it reports, then build.

Text fields accept a tiny, safe markdown: `` `code` ``, `**bold**`, `*italic*`, `x^{2}` (superscript), `B_{0}` (subscript), and line breaks. HTML is escaped, so don't use it.

```jsonc
{
  "meta": {
    "series": "Low-Field MRI Exam Series",   // same string every time, used to find earlier exams
    "number": 4,                               // position in the series
    "title": "Exam 4: SNR, B0 and hardware trade-offs",
    "date": "2026-11-09",
    "field": "Low-field MRI physics",
    "level": "Graduate",
    "professor": {
      "name": "Prof. Ada Lindqvist (persona)",
      "persona": "MR physicist focused on hardware and SNR trade-offs; Socratic; strict on units and assumptions"
    },
    "topics": ["Larmor frequency", "SNR scaling", "Noise sources"],
    "time_limit_minutes": 45,                  // null = untimed
    "instructions": "Answer all questions. Show units. State assumptions."
  },
  "questions": [
    {
      "id": "q1",                              // letters, digits, - or _; unique
      "type": "mc",                            // "mc" | "short" | "long"
      "concept": "Larmor frequency",           // REQUIRED: stable name, drives history and review
      "objective": "U1.1",                     // REQUIRED when a syllabus is used: syllabus objective id
      "objective_text": "Compute resonance frequencies…", // optional, shown in results
      "kind": "new",                           // review | new | transfer | pretest
      "bloom": "apply",                        // remember | understand | apply | analyze | evaluate | create
      "difficulty": 3,                         // 1-5, aim for an average of 3-4
      "hint": "Convert mT to T first. Which unit does γ/2π carry?", // optional Socratic nudge
      "points": 1,
      "prompt": "At B_{0} = 64 mT, what is the proton Larmor frequency?",
      "options": [
        {"id": "A", "text": "2.73 MHz"},
        {"id": "B", "text": "27.3 MHz"},
        {"id": "C", "text": "2.73 kHz"},
        {"id": "D", "text": "0.427 MHz"}
      ],
      "answer": "A",
      "explanation": "f = γ̄·B_{0} with γ̄ ≈ 42.58 MHz/T, so 42.58 × 0.064 ≈ 2.73 MHz.",
      "distractor_notes": {                    // why each wrong option is tempting
        "B": "Off by 10×: a decimal-place error in mT → T.",
        "C": "Unit slip: MHz/T × mT gives kHz only if B_{0} is left in mT.",
        "D": "Uses γ/2π for a different nucleus or divides instead of multiplying."
      },
      "sources": [
        {"title": "Marques JP, Simonis FFJ, Webb AG. Low-field MRI: An MR physics perspective. J Magn Reson Imaging. 2019;49(6):1528-1542",
         "url": "https://doi.org/10.1002/jmri.26637", "note": "Larmor relation and low-field context"}
      ]
    },
    {
      "id": "q2",
      "type": "short",                         // "long" has the same fields
      "concept": "SNR scaling with B0",
      "points": 4,
      "expected_length": "4-6 sentences",
      "answer_lines": 12,                      // optional: ruled lines on the printed paper
      "prompt": "Explain why SNR falls faster than linearly as B_{0} drops in the low-field regime.",
      "rubric": [                              // points MUST add up to the question's points
        {"criterion": "Signal scaling", "points": 2, "description": "Magnetization ∝ B_{0} and induced EMF ∝ ω_{0}, so signal ∝ B_{0}^{2}."},
        {"criterion": "Noise regime", "points": 2, "description": "At low field, coil/electronics noise dominates over sample noise, so noise doesn't fall with B_{0} the way it does at high field."}
      ],
      "model_answer": "…",                     // a strong reference answer
      "alternatives": "An answer framed around noise figure of the preamplifier, or around sample- vs coil-noise crossover frequency, is equally valid if the scaling argument is correct.",
      "sources": [ {"title": "…", "url": "…"} ]
    }
  ],
  "review_note": "Re-derived all MC keys independently; rewrote q3 because two options were defensible; balanced answer letters."
}
```

## syllabus.json

```jsonc
{
  "course": "Low-Field MRI Physics (graduate seminar)",
  "source": "Syllabus PDF, fall 2026",
  "units": [
    {
      "id": "U2",
      "title": "Signal, noise and relaxation at low field",
      "start": "2026-11-02", "end": "2026-11-15",          // ISO dates; derive them from week numbers if needed
      "readings": ["Marques et al. 2019, JMRI"],
      "objectives": [
        {"id": "U2.1", "text": "Derive how SNR scales with B0 in coil- and sample-noise regimes",
         "concept": "SNR scaling", "importance": "core"},       // core | supporting
        {"id": "U2.4", "text": "Estimate SAR changes across field strengths",
         "concept": "RF safety (SAR)", "importance": "supporting"}
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
