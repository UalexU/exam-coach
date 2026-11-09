---
name: exam-coach
description: Builds hard, research-backed practice exams (multiple choice with tricky near-miss distractors, short and long reasoning) aligned to a syllabus or learning path, written by a professor persona the user defines, as interactive timed artifacts or printable papers with answer keys, on a spaced recurring schedule (weekly by default). Use whenever someone wants to be quizzed, examined or tested on a subject, wants practice or mock exams, exam prep, spaced self-testing, a course-aligned study plan, or a recurring exam schedule, even if they don't say "exam".
license: MIT
---

# Exam Coach

Turn a field of study, or a course syllabus, into a steady rhythm of practice exams that teach. Each exam is written "by" a professor persona the user defines and follows the course's learning path. Every point tests a critical concept, every answer key is backed by real sources, and grading rewards sound reasoning over memorized phrasing. Exams can be taken in the browser (timed, auto-graded, color-coded) or printed and done by hand.

The point is learning, not trivia. A good exam is hard but fair: the learner has to think to separate the right answer from options that are almost right. Afterwards they see exactly where their reasoning held or broke, with the evidence.

Bundled files (paths relative to this skill's directory):

- `scripts/build_exam.py`: validates an exam JSON (rigor, alignment, balance) and renders every output. Standard library only; `--pdf` uses Playwright if present.
- `scripts/plan_next.py`: the learner model plus learning path. It turns past results (and a syllabus, if any) into a blueprint for the next exam.
- `assets/exam-template.html`: the interactive exam page. Don't rewrite it; fill it through the script.
- `references/exam-schema.md`: the exam JSON and syllabus JSON formats, and the validation rules. Read it before writing either.
- `references/question-craft.md`: how to write hard, fair questions and near-miss distractors. Read it before writing questions.
- `references/learning-science.md`: the evidence behind the loop and what's borrowed from Anki/FSRS, Duolingo, Khan Academy, ALEKS and others. Read it the first time you plan a series.

If `scripts/` or `assets/` are missing (the skill was saved as SKILL.md only), the workflow still applies. Install the full package (`exam-coach.skill`, or the `exam-coach` repository) to get them back. Until then, check the validation rules in section 6 by hand. Plan from history by reasoning over it: concepts last seen longest ago, missed, or missed while marked "Sure" come first. Build the outputs yourself: a self-contained interactive page with the features in section 7, or a printable paper and a separate key.

## The learning loop

Each exam is one turn of a loop, not a one-off quiz:

**syllabus / learning path** → **plan** (history + path) → **research** → **write** (hard, aligned, interleaved, new variants) → **review pass** → **take** (timed, confidence ratings, optional Socratic hints) → **feedback** (explanations, rubrics, sources, calibration, confident errors) → **reflect** → **save results** → plan the next exam.

Retrieval practice and spacing are the two study techniques with the strongest evidence. The series schedule, the per-concept memory model and the syllabus alignment aren't add-ons; they're how the skill teaches.

## 1. Gather the exam profile

If the request (or a scheduled-task prompt) already contains a profile, use it and don't ask again. Otherwise ask, in one round of questions where possible:

| Field | Default | Notes |
|---|---|---|
| Field / subject | (required) | e.g. "low-field MRI physics" |
| Professor persona | (required) | expertise, style, strictness, e.g. "MR physicist focused on hardware and SNR trade-offs, Socratic, strict on units" |
| Syllabus / learning path | strongly recommended | a course syllabus (file, pasted text, URL), a textbook's table of contents, or a list of units with dates (section 2) |
| Topics, readings, ideas | optional | papers, chapters, concepts, known weak spots |
| Level | graduate | undergrad / graduate / PhD qualifier / professional |
| Question mix | 10 multiple choice + 3 short reasoning + 1 long reasoning | reasoning questions are optional; MC-only is fine |
| Time limit | 45 min | adjustable, or untimed (`null`) |
| Output | interactive | `interactive`, `printable`, or `both` |
| Cadence | weekly | any interval, e.g. every 3 days (section 8) |
| Series name | "<Field> Exam Series" | used to find earlier exams |

Personas are fictional ("Prof. X (persona)"). Don't impersonate a real, named academic; "an applied Bayesian statistician who prizes model checking" is fine, a real professor's name is not.

If the user is clearly unavailable (scheduled or unattended run), use the defaults, state them at the top of your reply, and continue. When you set things up interactively, repeat the final profile back as one compact block so it can be pasted into a scheduled task.

## 2. Map the syllabus into a learning path

When the user gives a syllabus (or anything that orders the material), convert it once into `syllabus.json` (format in `references/exam-schema.md`):

- **Units** in teaching order, with start/end dates (or week numbers turned into dates from the course start).
- **Learning objectives** per unit, each written as an observable, testable outcome ("derive…", "predict…", "choose between… and justify"), with a stable `concept` name and an `importance` of `core` or `supporting`. Turn vague syllabus lines ("noise") into objectives a question can actually test. The critical concepts are the ones later units build on, the ones practitioners get wrong, and the ones the syllabus spends the most time on; mark those `core`.
- **Readings** per unit when listed, so research can start from them.

Show the user the extracted path (units → objectives) for a quick confirmation the first time, then save it alongside the series (in their folder, or say what to keep). Reuse it for every exam. If there's no syllabus, build a short learning path yourself from the profile's topics (foundational → applied → integrative) and say so. Leave `start`/`end` empty in a self-built path: unit dates are what make an objective "not yet taught", and invented dates would either block or unlock material arbitrarily.

With a path, exams follow it: credit items test objectives already taught (current unit and earlier). One low-stakes **pretest** item may preview the next unit. Nothing from later units is examined for credit.

## 3. Plan from history and path

Collect past results into `history.json` (a JSON list of result records). They can come from three places:

- the `results` collection of earlier exam artifacts in the series, when the `db` capability was granted (read it with the artifact data tool);
- results the learner pasted from the page's **Copy results for next exam** button, or a graded paper score sheet they sent back;
- a `history.json` the user keeps in a connected folder. Append the new record there after each exam if the user has one.

Then run (use `-` as history for the first exam):

```bash
python <skill-dir>/scripts/plan_next.py history.json --syllabus syllabus.json --questions <n>
```

It reports, per concept, the predicted recall today, stability, difficulty, streak and confident errors, plus a **blueprint**:

- how many items are spaced review, new and transfer;
- which concepts to review (confident errors first);
- which objectives the new items must test (current unit first, then any earlier untested ones);
- whether to add one pretest item from the next unit;
- whether to raise, hold or ease difficulty. The target is a 65-85% success rate: hard enough that thinking is required, not so hard that it's guessing.

Follow the blueprint unless the user asked for something specific. If every current-unit objective has already been tested, write harder, deeper variants of them (new scenarios, combined objectives) rather than drifting to untaught units. Read the learner's last reflection; if they said what tripped them up, test that. Look at the last two or three exams so reviewed concepts come back as **new variants** (new scenario, numbers or framing), never repeats.

## 4. Research before writing

Gather evidence before writing questions. For each objective you plan to test:

- Start from the syllabus readings if there are any, then search authoritative sources: textbooks, review papers, standards bodies, official documentation, and PubMed for biomedical topics. Prefer a recent review plus the seminal original paper.
- For every question, record 1-3 sources that support the keyed answer (title with authors/org and year, plus a DOI or URL).
- Note where the literature disagrees, where an answer depends on assumptions, and which misconceptions are documented. These are the raw material for hard questions and near-miss distractors.

If a claim can't be backed by a source you actually found, don't make it the keyed answer. Never invent citations or DOIs. If a source can't be verified, drop it. Fewer, well-sourced questions beat padding.

## 5. Write the exam

Read `references/question-craft.md` first. The short version:

### Every point tests a critical concept

- Each question maps to one `concept` and, with a syllabus, one `objective` (the validator enforces both). Spend points where they matter: core objectives should carry at least 60% of the points, and harder or more central ideas earn more.
- If a question would still be answerable by someone who doesn't understand the concept (by recall, keyword matching or test-taking tricks), it isn't testing the concept. Rewrite it.

### Hard but fair

- **No pure recall.** Default to `apply`, `analyze` and `evaluate`. Recall/understand items should be under a quarter of the exam, and only as pretests or stepping stones.
- **Scenario first.** Put the concept to work in a realistic situation: a protocol change, a dataset, a design decision, a result to interpret.
- **Near-miss distractors.** Every MC item has four options. At least two wrong options should be *almost right*: correct reasoning with one flaw, a true statement that doesn't answer the question, the right answer under a different assumption, or the documented misconception. The learner should have to reason to rule them out, not spot an obviously silly option. Every wrong option gets a `distractor_notes` entry naming its flaw (the validator enforces this).
- **Fair, not tricky.** Exactly one option is defensibly best given the stated assumptions. State every assumption the answer depends on. No double negatives, no "all/none of the above", no gotchas on wording. The difficulty comes from the thinking, never from parsing.
- Give each item a `difficulty` 1-5 and aim for an average of about 3-4.

### Question types

- **Multiple choice** (1 point each by default, 4 options, one best answer).
- **Short reasoning** (4 points by default, about 3-6 sentences): a scenario, derivation, prediction or critique. The rubric has 2-4 criteria with points.
- **Long reasoning** (10 points by default, about 1-2 pages): design an experiment, critique a method, compare approaches under constraints, or defend a position. Rubric criteria typically cover core concepts, quality of argument, use of evidence, trade-offs and limitations, and originality.

Optional `hint`: a Socratic nudge in the persona's voice that points to the right line of reasoning without giving the answer. Hint use is recorded and counts as weaker evidence of mastery.

Write in the professor persona's voice: its preoccupations, its standards, its favorite kinds of problems.

Also tag `kind` (`review`, `new`, `transfer`, `pretest`) and `bloom` on every item. Interleave: neighbouring questions should test different concepts, and the hardest items shouldn't all sit at the end.

### Critical thinking comes first

The answer key is a reference, not a cage:

- Rubrics state what a strong answer must *demonstrate*, not a required wording.
- Every reasoning question gets an `alternatives` line describing other defensible approaches. A well-argued answer that reaches a different but defensible conclusion earns full or near-full credit.
- Give partial credit for correct reasoning with an arithmetic slip, and for naming the right principle even when the conclusion is off.
- MC explanations say why the key is right *and* why each distractor is tempting but wrong.

## 6. Review pass (every time)

Before building, audit the exam as a skeptical second examiner:

1. Re-solve each MC item without looking at the key. If you get a different answer, or two options are defensible, rewrite it.
2. Try to answer each item *without* understanding the concept (elimination, length cues, keyword matching). If that works, harden it.
3. Check each distractor is plausible to someone with a partial understanding. Replace any option nobody would pick.
4. Check that each source supports the specific claim it's cited for.
5. Check for ambiguity, unstated assumptions and units.
6. Check alignment and balance: objectives covered match the blueprint, points weighted toward core objectives, answer letters spread, and a realistic time limit (about 1.5-2 min per hard MC, 5-7 per short, 15-25 per long).

Record what you changed and why in `review_note`. Then run the validator; it catches the mechanical problems (alignment, rubric sums, missing distractor notes, too many recall items, give-away lengths, unbalanced letters, blocked ordering):

```bash
python <skill-dir>/scripts/build_exam.py exam.json --check --syllabus syllabus.json
```

Fix every error and address warnings unless there's a stated reason not to.

## 7. Build the output

```bash
python <skill-dir>/scripts/build_exam.py exam.json --out <dir> [--pdf] [--syllabus syllabus.json]
```

This writes:

| File | Use |
|---|---|
| `exam.artifact.html` | page body to publish with the Artifact tool (the tool adds the doctype and head) |
| `exam.html` | the same page as a standalone file, for local use or when publishing isn't available |
| `paper.html` / `paper.pdf` | printable paper: name/date/score header, bubbles for MC, ruled space for reasoning, G/U/S confidence marks per question |
| `key.html` / `key.pdf` | answer key with the paper's numbering: color legend, score sheet (concept, objective, points, ✓/½/✗, confidence), keyed answers, distractor notes, rubrics, alternatives, sources, review note |

### Interactive (default)

Publish `exam.artifact.html` with the Artifact tool, titled `<Series> #<n>: <topic>`. Declare `capabilities: {"sample": {}, "db": {}, "user": {}}` when the account offers them (load the `artifact-capabilities` skill first if it's available). `sample` turns on **Grade with Claude** for written answers, and `db` saves results for the next exam to read. The page works without them: written answers fall back to rubric self-scoring.

What the page does, so you can describe it accurately:

- Start screen with persona, topics, point totals and an adjustable time limit; the timer starts on **Start**, not on load.
- A Guess / Unsure / Sure confidence rating and an optional **Ask the professor for a nudge** hint on each question.
- Sticky countdown (amber at 10 min, red at 2 min), progress bar, jump-to grid, flag-for-review, autosave in the browser.
- Auto-submit at time-out with a banner; manual submit warns about unanswered questions.
- Results: score ring, per-section totals, and every question marked **✓ Correct** (green), **½ Partial** (amber) or **✗ Incorrect** (red) with points earned, its concept and objective. MC shows the chosen and correct options. Written answers show rubric rows scored Full/Half/None, examiner feedback, the reference answer, alternatives and linked sources. A "what to review next" list is built from the weak concepts.
- A confidence check (accuracy per confidence level) and a red callout on every **confident error**. Fixing a belief you were sure about tends to stick (the hypercorrection effect), so these come first in the next exam.
- A one-minute reflection box and a **Copy results for next exam** button (JSON for `history.json`). With `db`, results and reflection save automatically.
- Light and dark themes, phone-width layout, keyboard accessible, color always paired with icon and text, print-friendly.

The answer key sits in the page's data until submission. This is practice, not proctoring.

### Printable

Deliver `paper.pdf` and `key.pdf` (or the `.html` files if PDF export isn't available). Keep the key separate so the learner doesn't see it while working. Ask the learner to send back the score sheet (or a photo of it) so the next exam can be planned from it.

If the environment has no Python, write the same content by hand: the interactive page is still `assets/exam-template.html` with `__EXAM_TITLE__` and `__EXAM_JSON__` replaced (escape `</` as `<\/` inside the JSON).

## 8. Scheduling

For recurring exams, create a scheduled task with the platform's scheduling tool (in Claude apps, `create_trigger`; never a session-local cron that disappears when the session ends). Weekly is the default; use any interval the user asks for. Write cron in the user's time zone with `CRON_TZ=`, avoid minute `0`, and avoid 6-9 AM Pacific, when runs are often delayed.

- Weekly: `CRON_TZ=<tz> 23 18 * * 0`
- Every 3 days: `CRON_TZ=<tz> 23 18 */3 * *`. Day-of-month steps restart each month (the 31st and the 1st are one day apart). For exact spacing, tell the run to skip if the last exam in the series is less than N days old.

Each run starts fresh, so the scheduled prompt must contain everything:

> Use the exam-coach skill to create the next exam in the series "<series>". Profile: <full profile block>. Syllabus: <path to syllabus.json, or the units/objectives inline>. Gather results from earlier exams in this series (their saved results, or <path to history.json>), run plan_next.py with the syllabus and follow its blueprint. Deliver as <output>. When it's ready, send me a short message with the link and the objectives it covers.

Afterwards, tell the user the schedule in plain words and which approval setting the task got.

## 9. Wrap-up

One or two sentences: which unit and objectives the exam covers, its length and time limit, and the link or files. Don't reveal answers in chat.
