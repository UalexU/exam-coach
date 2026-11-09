# Contributing

Thanks for helping make practice exams teach better.

## Ground rules

- **Learning first.** Changes to the loop (scheduling, difficulty, feedback) should point to evidence or to a tool that demonstrably does it well. Add the reference to `skills/exam-coach/references/learning-science.md`.
- **No runtime dependencies.** Scripts use only the Python standard library (3.9+); the exam page uses no external scripts, fonts or CDNs.
- **Explain the why in SKILL.md.** Claude follows reasons better than rules in capitals.
- **Never fabricate sources** in examples or tests.

## Workflow

1. Fork and branch from `main`.
2. Make the change. If you change the exam JSON or syllabus format, update `references/exam-schema.md` and the examples.
3. Run `make test` and, for template or build changes, `make test-ui`.
4. If behaviour changed, add or update an eval case in `skills/exam-coach/evals/` (one assertion per file in `graders/`).
5. Update `CHANGELOG.md` and open a pull request.

## Project structure

See the [README](README.md#repository-layout).
