# Security policy

## Reporting a vulnerability

Please report security issues privately via GitHub's **Report a vulnerability** (Security tab) rather than in a public issue. You'll get a response within a week.

## Scope notes

- The exam page renders exam text through an escape-first formatter and embeds exam data with `</` escaped, so exam content can't inject script. Reports of bypasses are welcome.
- Results saved through the artifact `db` capability are visible to people the artifact is shared with. Don't share an exam artifact if your results are private.
- The answer key ships inside the interactive page's data. This is a practice tool, not a proctoring system.
