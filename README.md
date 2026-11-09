# Exam Coach

**A Claude skill that turns any subject, or your course syllabus, into hard, research-backed practice exams on a spaced schedule, and learns from every attempt.**

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![No runtime dependencies](https://img.shields.io/badge/runtime%20deps-none-brightgreen.svg)

<p align="center">
  <img src="docs/images/results-light.png" width="62%" alt="Results page: score ring, confidence check, color-coded answers">
  <img src="docs/images/results-dark-mobile.png" width="27%" alt="Results on a phone in dark mode">
</p>

You give it a field, a professor persona and (ideally) a syllabus. Every few days it writes an exam that:

- **tests only what matters**: every point maps to a critical concept and a syllabus objective, weighted toward core objectives;
- **is hard but fair**: scenario-based apply/analyze/evaluate items, with near-miss distractors you have to reason past;
- **is backed by real sources**: every keyed answer cites a checked paper, textbook or standard, never an invented DOI;
- **rewards critical thinking**: rubrics grade the argument, and defensible alternative answers earn credit;
- **teaches through feedback**: ✓ correct / ½ partial / ✗ incorrect with points, why each wrong option is tempting, a confidence check that flags *confident errors*, and a reflection prompt;
- **plans the next exam from your results**: an FSRS-style memory model per concept brings back what you're about to forget, puts confident errors first, and only graduates a concept after three spaced successes.

Take it in the browser (timed, autosaved, auto-graded, light/dark, phone-friendly) or print the paper and a separate answer key.

## Contents

- [How it works](#how-it-works)
- [Install](#install)
- [Use](#use)
- [What you get](#what-you-get)
- [The learning science](#the-learning-science)
- [Repository layout](#repository-layout)
- [Development](#development)
- [Test results](#test-results)
- [License](#license)

## How it works

```
syllabus.json ─► plan_next.py ─► research ─► write exam.json ─► review pass ─► build_exam.py --check
  (learning      (history +       (papers,      (hard, aligned,      (re-solve,        │
   path)          spacing)         PubMed)       interleaved)          harden)          ▼
       ▲                                                                       interactive page
       │                                                                       or paper + key
       └──── history.json ◄── results (score, confidence, hints, reflection) ◄── you take it
```

1. **Profile**: field, a fictional professor persona (expertise, style, strictness), level, question mix, time limit (default 45 min), output, and cadence (default weekly).
2. **Learning path**: your syllabus becomes `syllabus.json` (units, dates, testable objectives marked core/supporting). Exams only give credit for what's already been taught; one low-stakes pretest item may preview the next unit.
3. **Plan**: `plan_next.py` reads your past results and returns a blueprint: spaced review vs new vs transfer items, which objectives to test, confident errors to fix first, and whether to raise or ease difficulty (target 65-85% success).
4. **Research → write → review**: Claude finds sources, writes items in the persona's voice, then audits them as a skeptical second examiner (re-solves every item, tries to "game" each one, checks every citation).
5. **Validate & build**: `build_exam.py` enforces the rules (alignment, distractor notes, recall cap, rubric sums, letter balance, interleaving) and renders the outputs.
6. **Schedule**: a scheduled task repeats the loop every N days (e.g. every 3 days).

## Install

**Claude apps (claude.ai / desktop / Cowork):** download `exam-coach.skill` from the [latest release](../../releases) or build it with `make package`, then upload it under **Settings → Capabilities → Skills**.

**Claude Code:** this repo is also a plugin marketplace:

```bash
/plugin marketplace add <owner>/exam-coach
/plugin install exam-coach@exam-coach
```

or copy `skills/exam-coach/` into `~/.claude/skills/`.

Requirements: Python 3.9+ (standard library only). Optional: Playwright + Chromium for PDF export.

## Use

Just ask. For example:

> Here's my syllabus for *Low-Field MRI Physics*. Every 3 days, give me a 40-minute exam (10 multiple choice, 2 short reasoning, 1 long reasoning) written by an MR hardware physicist who's Socratic and strict about units. Make it hard.

> Plan exam #4 from my history.json, printable with a separate answer key.

> Quick: 8 untimed multiple-choice questions on Bayesian model checking.

Claude asks for anything missing (field, persona, syllabus), shows you the extracted learning path once, builds the exam, and offers to schedule the series.

### Running the scripts yourself

```bash
# what should the next exam contain?
python skills/exam-coach/scripts/plan_next.py examples/sample-history.json \
  --syllabus examples/sample-syllabus.json --today 2026-11-06 --questions 12

# validate and build (interactive page, paper, key, PDFs)
python skills/exam-coach/scripts/build_exam.py examples/sample-exam.json \
  --syllabus examples/sample-syllabus.json --out exam-out --pdf
```

```
Next exam (2026-11-06): 12 questions = 2 spaced review + 7 new + 2 transfer
Difficulty: hold: the learner is in the productive 65-85% range (recent avg 0.83)
Learning path: now in U2 Signal, noise and relaxation at low field; next U3 Portable systems and hardware (2026-11-16)
1 pretest (low-stakes preview): U3.1 Portable systems
Confident errors to fix first: Gradient design, Relaxation vs field
```

## What you get

| Output | What it is |
|---|---|
| Interactive exam | Start screen; adjustable timer that starts on **Start**; auto-submit on time-out; Guess/Unsure/Sure confidence; optional *Ask the professor* Socratic hint; flag for review; jump grid; autosave |
| Results | Score ring and section totals; ✓/½/✗ per question with points, concept and objective; explanations and distractor notes; rubric scoring (self or **Grade with Claude**); sources; confidence calibration; confident-error callouts; "what to review next"; reflection; **Copy results** for the next plan |
| `paper.pdf` | Name/date/score header, MC bubbles, ruled answer space, G/U/S confidence marks |
| `key.pdf` | Same numbering as the paper; color legend; score sheet with concept, objective, ✓/½/✗ and G/U/S columns; answers, rubrics, alternatives, sources, examiner's review note |

<p align="center">
  <img src="docs/images/exam-light.png" width="48%" alt="Exam in progress with timer and confidence buttons">
  <img src="docs/images/paper.png" width="34%" alt="Printable exam paper">
</p>

When published as a Claude artifact with the `sample` and `db` capabilities, written answers can be graded by Claude against the rubric, and results are saved for the next exam. Without them, everything still works: written answers are self-scored against the rubric and results are copied.

## The learning science

Each feature maps to evidence. Full table and citations: [`references/learning-science.md`](skills/exam-coach/references/learning-science.md).

| Principle | Implemented as |
|---|---|
| Retrieval practice + spacing (Dunlosky et al. 2013; Cepeda et al. 2008) | the exam *is* the study session; recurring schedule; per-concept recall prediction |
| FSRS memory model (Anki) | stability / difficulty / retrievability per concept, target retention 0.9 |
| Successive relearning (Rawson & Dunlosky) | mastery = 3 spaced successful sessions with stability ≥ 21 days |
| Interleaving (Rohrer & Taylor 2007) | neighbouring items test different concepts; transfer items mix concepts |
| Hypercorrection (Butterfield & Metcalfe 2001) | confidence ratings, calibration table, confident errors first next time |
| Desirable difficulty | apply-level-or-higher items, near-miss distractors, 65-85% success target |
| Pretesting (Richland et al. 2009) | one low-stakes preview item from the next unit |
| Constructive alignment (Biggs 1996) | every item ↔ syllabus objective; credit only for taught material |
| Elaboration, feedback, reflection | reasoning questions; explanation of every option; one-minute reflection |

How to write the questions: [`references/question-craft.md`](skills/exam-coach/references/question-craft.md).

## Repository layout

```
skills/exam-coach/
├── SKILL.md                     # the skill: workflow Claude follows
├── assets/exam-template.html    # interactive exam page (no external deps)
├── scripts/build_exam.py        # validator + renderer (HTML, paper, key, PDF)
├── scripts/plan_next.py         # learner model + learning path → blueprint
├── references/                  # exam/syllabus schema, question craft, learning science
└── evals/                       # test cases (claude plugin eval format)
examples/                        # sample exam, syllabus and history
tests/                           # unit tests + Playwright browser test
.claude-plugin/                  # Claude Code plugin + marketplace manifests
```

## Development

```bash
make test       # unit tests (stdlib only)
make test-ui    # browser test (pip install -r requirements-dev.txt && python -m playwright install chromium)
make validate   # validate the example exam against the example syllabus
make example    # build example outputs into exam-out/
make package    # dist/exam-coach.skill
```

The skill's own test cases live in `skills/exam-coach/evals/` and run with `claude plugin eval skills/exam-coach --allow-tools Write,Edit,Bash,WebSearch,WebFetch --scaffold`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Test results

The skill was evaluated with and without the skill on four realistic prompts (interactive exam, printable exam planned from history, quick untimed MC quiz, and a syllabus-aligned "make it hard" exam):

| | With skill | Without skill |
|---|---|---|
| Assertions passed (iteration 2) | **100%** | 72.5% |
| Questions with a checked source | **100%** | 0-83% |
| Recall-only items (rerun) | **0** | n/a |
| Mean difficulty (rerun) | **3.8 / 5** | n/a |

Details in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE) © 2026 Alex Villalba Gonzalez. Exams you generate are yours. Cited sources keep their own licenses; exams link to them rather than reproducing them.
