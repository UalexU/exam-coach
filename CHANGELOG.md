# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-06

### Added
- `exam-coach` skill: profile → learning path → plan → research → write → review → build → schedule.
- Syllabus support (`syllabus.json`): units with dates, testable objectives marked core/supporting; credit only for taught material, one optional pretest from the next unit; alignment checks in the validator.
- `plan_next.py`: FSRS-4.5-style per-concept memory model (stability, difficulty, retrievability), successive-relearning mastery rule, confident-error priority, hint-weighted evidence, difficulty targeting (65-85%), and learning-path blueprint.
- `build_exam.py`: validator (alignment, distractor notes for every wrong option, recall cap, difficulty, rubric sums, letter balance, interleaving, give-away lengths, time estimate) and renderer (interactive page, printable paper, answer key, optional PDF).
- Interactive exam page: timer with auto-submit, confidence ratings, Socratic hints, flags, autosave, ✓/½/✗ results with points, rubric self-grading or Claude grading, calibration table, confident-error callouts, reflection, results export, `db` result saving, light/dark, mobile, print.
- References: exam and syllabus schema, question craft, learning science.
- Four eval cases, unit tests, Playwright browser test, CI.

### Evaluation
- Iteration 1 (3 prompts × with/without skill): 100% vs 66.7% assertions passed. Found a paper/key numbering bug and missing confidence capture on paper.
- Iteration 2 (added syllabus case, rigor rules, hints, print fixes): 100% vs 72.5%. Rerun produced 0 recall-only items and mean difficulty 3.8/5.
