# The learning loop: why the skill works the way it does

Each feature below exists because there's good evidence for it, or because the best learning software already proves it works. Read this when you plan the next exam in a series or have to explain a design choice to the user.

## Principles and how the skill applies them

| Principle | Evidence | What exam-coach does |
|---|---|---|
| **Retrieval practice** (the testing effect) | Practice testing and distributed practice were the only two techniques rated "high utility" across learners, materials and settings in Dunlosky et al. (2013, *Psychological Science in the Public Interest* 14(1):4-58). | The exam itself is the study session. Every question asks the learner to produce or choose an answer from memory, never to re-read. |
| **Spacing** | The best gap between sessions grows with how long you need to remember: about 10-20% of the retention interval for short horizons, a smaller fraction for longer ones (Cepeda, Vul, Rohrer, Wixted & Pashler 2008, *Psychological Science* 19(11):1095-1102). | Exams recur on a schedule (every 3-7 days), and `plan_next.py` brings back each concept when its predicted recall drops below 90%. |
| **Memory model / adaptive scheduling** | FSRS, now built into Anki, models each item's stability, difficulty and retrievability. It schedules more efficiently than the older SM-2 algorithm at the same retention. | `plan_next.py` keeps a per-concept stability, difficulty and recall estimate using the FSRS-4.5 forgetting curve R = (1 + 19/81 · t/S)^-0.5. |
| **Successive relearning** | Retrieving to criterion, then relearning across several spaced sessions, gives durable retention; three spaced successful sessions is a common target (Rawson & Dunlosky; review in *Current Directions in Psychological Science*, 2022). | A concept is "mastered" only after three spaced sessions at ≥ 80% with stability ≥ 21 days. Until then it keeps coming back. |
| **Interleaving** | Mixing problem types makes the learner choose the strategy, not just execute it. Shuffled practice beat blocked practice on a delayed test (Rohrer & Taylor 2007, *Instructional Science* 35:481-498). | Questions on the same concept aren't placed next to each other (the validator warns). "Transfer" items deliberately combine an old concept with a new one. |
| **Feedback with explanation** | Corrective feedback that explains *why* improves retention more than right/wrong alone. Feedback after a short delay (end of test) works well for MC. | Results show the key, why each distractor is tempting, rubric criteria, a reference answer, alternatives and sources. |
| **Confidence and hypercorrection** | Errors made with high confidence are *more* likely to be corrected after feedback than low-confidence errors (Butterfield & Metcalfe 2001, *JEP: LMC* 27(6):1491-1494). Rating confidence also trains metacognitive calibration. | Each question has Guess / Unsure / Sure. Results show a calibration table and flag "confident errors" first. `plan_next.py` puts those concepts at the front of the next exam. |
| **Desirable difficulty (65-85% success)** | Learning is fastest when tasks are hard enough to produce some errors (Bjork's desirable difficulties). A model-based estimate puts the sweet spot near 85% accuracy (Wilson et al. 2019, *Nature Communications* 10:4646). | Items default to apply/analyze level with near-miss distractors. `plan_next.py` raises difficulty when recent scores are above 85% and eases it below 65%; we deliberately sit a little below the 85% optimum because exam items carry several concepts at once. |
| **Pretesting** | Attempting questions on material *before* studying it improves later learning, even when the first attempt fails (Richland, Kornell & Kao 2009, *JEP: Applied* 15(3):243-257). | New topics can enter as low-stakes "preview" items (`kind: "pretest"`), labelled so a miss isn't discouraging. |
| **Elaboration and self-explanation** | Explaining *why* (elaborative interrogation, self-explanation) is rated moderate utility and is what reasoning questions require. | Short and long reasoning questions grade the argument, and the rubric rewards defensible alternatives (critical thinking first). |
| **Higher-order thinking** | Recall-only tests produce recall-only learning; applying and analyzing items transfer better. | Every question gets a Bloom level. The validator warns if more than half are recall/understand. |
| **Metacognitive reflection** | A short "what will I change?" reflection after feedback improves later study choices (exam wrappers). | The results page ends with a one-minute reflection that's saved with the results and read when the next exam is planned. |
| **Constructive alignment** | Learning outcomes, teaching activities and assessment should all target the same objectives (Biggs 1996, *Higher Education* 32:347-364). Assessment that drifts from the objectives teaches the wrong thing. | Exams follow `syllabus.json`: every question maps to an objective, credit items only test what's been taught, and points are weighted toward core objectives. |
| **Mastery learning** | Tutoring plus mastery-based progression gives large gains (Bloom 1984, "the 2 sigma problem"). Khan Academy and ALEKS structure progress around mastery. | Concepts graduate on mastery evidence, not on calendar time. Weak prerequisites come back before new topics build on them. |

## What the best tools do, and what we borrow

| Tool | What it's best at | Borrowed |
|---|---|---|
| **Anki (FSRS)** | Per-item memory model, optimal review timing | Stability/difficulty/recall model per concept, target retention 0.9 |
| **SuperMemo** | Origin of algorithmic spacing; "20 rules of formulating knowledge" (minimum information principle) | One idea per MC item; no compound questions |
| **Duolingo** | Half-life regression (Settles & Meeder 2016) predicts forgetting per item; streaks and short sessions | Forgetting-based selection; short, frequent sessions; visible progress |
| **Khan Academy / ALEKS** | Mastery levels; Knowledge Space Theory finds what the learner is ready to learn next | Mastery gate; prerequisites before new material |
| **Brilliant** | Learning by solving and reasoning, not by reading | Reasoning questions; scenarios; "explain why" |
| **Quizlet Learn / RemNote** | Adaptive question formats; notes linked to review | Mixed formats; concept tags link results to topics |
| **Gradescope / PrairieLearn** | Rubric-based grading, consistent partial credit; question variants | Explicit rubric rows with points; Full/Half/None scoring; fresh variants of reviewed concepts instead of identical repeats |

## The loop in one picture

```
syllabus.json ─► profile ─► plan_next.py (history → blueprint) ─► research ─► write exam ─► review pass + --check
   ▲                                                                              │
   │                                                                              ▼
history.json / db results ◄── results page (score, confidence, reflection) ◄── take exam
```

## Practical rules that follow

- Reviewed concepts come back as **new variants** (a new scenario, numbers or framing), never the identical item. Otherwise the learner memorizes the answer, not the idea.
- Put **confident errors** first and test them again in a different form.
- Keep each session short enough to finish (30-60 min). Frequent short exams beat rare long ones.
- Spread the effort: about 55% spaced review, 30% new, 15% transfer/interleaving. In the first two or three exams there's little to review, so most items are new.
- Make the explanation the teaching moment: an explanation that only restates the key is a wasted opportunity.
