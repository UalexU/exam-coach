#!/usr/bin/env python3
"""Validate an exam JSON file and render it.

Outputs (written next to --out, default ./exam-out/):
  exam.artifact.html  page body for the Artifact tool (no doctype; the tool adds it)
  exam.html           full standalone page (open locally, or share as a file)
  paper.html          printable exam paper (no answers)
  key.html            printable answer key + rubrics + sources + examiner's review
  paper.pdf, key.pdf  only with --pdf (needs Playwright + Chromium)

Usage:
  python build_exam.py exam.json [--out DIR] [--pdf] [--check]
  --check   validate only, print problems, exit 1 on errors
Standard library only (Playwright optional for --pdf).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "exam-template.html"
TYPES = {"mc", "short", "long"}
KINDS = {"review", "new", "transfer", "pretest"}
BLOOM = ["remember", "understand", "apply", "analyze", "evaluate", "create"]


# ---------------------------------------------------------------- validation
def validate(exam: dict, syllabus: dict | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). With a syllabus, also check objective alignment and coverage."""
    E: list[str] = []
    W: list[str] = []
    meta = exam.get("meta")
    qs = exam.get("questions")
    if not isinstance(meta, dict):
        E.append("meta: missing or not an object")
        meta = {}
    if not isinstance(qs, list) or not qs:
        E.append("questions: missing or empty")
        qs = []
    for k in ("title", "field"):
        if not meta.get(k):
            E.append(f"meta.{k}: required")
    prof = meta.get("professor") or {}
    if not prof.get("persona"):
        W.append("meta.professor.persona: empty (the persona drives question style)")
    tl = meta.get("time_limit_minutes")
    if tl is not None and (not isinstance(tl, (int, float)) or tl <= 0):
        E.append("meta.time_limit_minutes: must be a positive number or null (untimed)")

    ids = Counter(q.get("id") for q in qs if isinstance(q, dict))
    for d, n in ids.items():
        if n > 1:
            E.append(f"duplicate question id: {d}")
    keys = []
    est_minutes = 0.0
    for i, q in enumerate(qs, 1):
        p = f"questions[{i}] ({q.get('id', '?')})"
        if not isinstance(q, dict):
            E.append(f"{p}: not an object")
            continue
        if not q.get("id") or not re.fullmatch(r"[A-Za-z0-9_-]+", str(q.get("id"))):
            E.append(f"{p}: id must be letters, digits, - or _")
        t = q.get("type")
        if t not in TYPES:
            E.append(f"{p}: type must be one of {sorted(TYPES)}")
            continue
        if not q.get("prompt"):
            E.append(f"{p}: prompt required")
        pts = q.get("points")
        if not isinstance(pts, (int, float)) or pts <= 0:
            E.append(f"{p}: points must be > 0")
        if q.get("kind") and q["kind"] not in KINDS:
            E.append(f"{p}: kind must be one of {sorted(KINDS)}")
        if q.get("bloom") and q["bloom"] not in BLOOM:
            W.append(f"{p}: bloom should be one of {BLOOM}")
        if not q.get("concept"):
            E.append(f"{p}: concept required: every point must map to a named critical concept")
        d = q.get("difficulty")
        if d is not None and d not in (1, 2, 3, 4, 5):
            E.append(f"{p}: difficulty must be 1-5")
        if q.get("bloom") == "remember" and q.get("kind") != "pretest":
            W.append(f"{p}: pure recall item: rewrite it so the learner has to apply or reason")
        if not q.get("sources"):
            W.append(f"{p}: no sources: every keyed answer should be backed by evidence")
        for s in q.get("sources") or []:
            if not s.get("title"):
                E.append(f"{p}: every source needs a title")
        if t == "mc":
            est_minutes += 1.25
            opts = q.get("options") or []
            oids = [o.get("id") for o in opts]
            if len(opts) < 3:
                E.append(f"{p}: multiple choice needs at least 3 options")
            elif len(opts) < 4:
                W.append(f"{p}: use 4 options so there's room for two near-miss distractors")
            if len(set(oids)) != len(oids):
                E.append(f"{p}: option ids must be unique")
            if q.get("answer") not in oids:
                E.append(f"{p}: answer '{q.get('answer')}' is not one of the option ids {oids}")
            else:
                keys.append(q["answer"])
                lens = {o["id"]: len(o.get("text", "")) for o in opts}
                longest = max(lens, key=lens.get)
                others = [v for k, v in lens.items() if k != longest]
                if longest == q["answer"] and others and lens[longest] > 1.6 * max(others):
                    W.append(f"{p}: keyed option is much longer than the others (give-away cue)")
            if not q.get("explanation"):
                E.append(f"{p}: explanation required")
            dn = q.get("distractor_notes") or {}
            missing = [o for o in oids if o != q.get("answer") and not dn.get(o)]
            if missing:
                E.append(f"{p}: distractor_notes missing for {missing}: every wrong option must encode a named misconception or flaw")
            txt = " ".join(o.get("text", "").lower() for o in opts)
            if "all of the above" in txt or "none of the above" in txt:
                W.append(f"{p}: avoid 'all/none of the above'")
        else:
            est_minutes += 6 if t == "short" else 20
            rub = q.get("rubric") or []
            if not rub:
                E.append(f"{p}: rubric required for reasoning questions")
            total = sum(r.get("points", 0) for r in rub)
            if rub and abs(total - (pts or 0)) > 1e-6:
                E.append(f"{p}: rubric points ({total}) must add up to question points ({pts})")
            for r in rub:
                if not r.get("criterion"):
                    E.append(f"{p}: every rubric row needs a criterion")
            if not q.get("model_answer"):
                E.append(f"{p}: model_answer required")
            if not q.get("alternatives"):
                W.append(f"{p}: no 'alternatives': list other defensible approaches so critical thinking is rewarded")

    if len(keys) >= 6:
        c = Counter(keys)
        top, n = c.most_common(1)[0]
        if n / len(keys) > 0.45:
            W.append(f"answer key is unbalanced: '{top}' is correct in {n}/{len(keys)} MC items")
    if tl and est_minutes > tl * 1.25:
        W.append(f"time limit {tl} min looks tight (rough estimate {est_minutes:.0f} min)")
    bl = [q.get("bloom") for q in qs if isinstance(q, dict) and q.get("bloom") and q.get("kind") != "pretest"]
    if len(bl) >= 4 and sum(x in ("remember", "understand") for x in bl) / len(bl) > 0.25:
        W.append("over 25% of items are recall/understand level: the exam is too easy; rewrite them as apply/analyze/evaluate")
    ds = [q.get("difficulty") for q in qs if isinstance(q, dict) and q.get("difficulty") in (1, 2, 3, 4, 5)]
    if len(ds) >= 4 and sum(ds) / len(ds) < 3:
        W.append(f"mean difficulty {sum(ds)/len(ds):.1f}/5 is low: aim for about 3-4 (hard but fair)")
    if syllabus:
        _check_syllabus(exam, syllabus, E, W)
    order = [q.get("concept") for q in qs if isinstance(q, dict) and q.get("type") == "mc" and q.get("concept")]
    runs = sum(1 for x, y in zip(order, order[1:]) if x == y)
    if len(order) >= 6 and runs / (len(order) - 1) > 0.5:
        W.append("MC items are blocked by concept: interleave them so neighbouring questions test different concepts")
    if not exam.get("review_note"):
        W.append("review_note: missing: record what the examiner's review pass changed")
    return E, W


def syllabus_index(syllabus: dict) -> dict:
    idx = {}
    for u in syllabus.get("units", []):
        for o in u.get("objectives", []):
            idx[o["id"]] = dict(o, unit=u)
    return idx


def _check_syllabus(exam: dict, syllabus: dict, E: list, W: list) -> None:
    idx = syllabus_index(syllabus)
    qs = [q for q in exam.get("questions", []) if isinstance(q, dict)]
    exam_date = (exam.get("meta") or {}).get("date") or ""
    covered, pts_core, pts_all = set(), 0.0, 0.0
    for q in qs:
        o = q.get("objective")
        p = f"question {q.get('id', '?')}"
        if not o:
            E.append(f"{p}: objective required when a syllabus is given (map it to a syllabus objective id)")
            continue
        if o not in idx:
            E.append(f"{p}: objective '{o}' is not in the syllabus")
            continue
        covered.add(o)
        pts_all += q.get("points", 0)
        if idx[o].get("importance", "core") == "core":
            pts_core += q.get("points", 0)
        start = idx[o]["unit"].get("start") or ""
        if exam_date and start and start > exam_date and q.get("kind") != "pretest":
            W.append(f"{p}: objective {o} is taught after {exam_date}: mark it kind 'pretest' or drop it")
    if pts_all and pts_core / pts_all < 0.6:
        W.append(f"only {pts_core/pts_all:.0%} of points test core objectives: weight the critical concepts more")
    if exam_date:
        cur = [u for u in syllabus.get("units", []) if (u.get("start") or "") <= exam_date <= (u.get("end") or "9999")]
        for u in cur:
            miss = [o["id"] for o in u.get("objectives", []) if o.get("importance", "core") == "core" and o["id"] not in covered]
            if miss:
                W.append(f"current unit {u.get('id')} core objectives not tested: {miss}")


# ---------------------------------------------------------------- rendering
def _inline_json(exam: dict) -> str:
    s = json.dumps(exam, ensure_ascii=False)
    # never let data close the <script> element
    return s.replace("</", "<\\/").replace("<!--", "<\\!--")


def render_interactive(exam: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    title = html.escape(exam["meta"].get("title", "Exam"))
    return tpl.replace("__EXAM_TITLE__", title).replace("__EXAM_JSON__", _inline_json(exam))


def standalone(fragment: str) -> str:
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '</head><body>' + fragment + '</body></html>')


def _md(s: str) -> str:
    s = html.escape(s or "")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(^|[^*])\*([^*\n]+)\*", r"\1<em>\2</em>", s)
    s = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", s)
    return s.replace("\n", "<br>")


PRINT_CSS = """
@page{size:Letter;margin:18mm 16mm}
*{box-sizing:border-box}body{font:11pt/1.5 Georgia,'Times New Roman',serif;color:#111;margin:0}
h1{font:700 20pt/1.2 ui-sans-serif,system-ui,sans-serif;margin:0 0 4pt}
h2{font:700 12pt ui-sans-serif,system-ui,sans-serif;margin:18pt 0 6pt;border-bottom:1.5pt solid #111;padding-bottom:3pt}
.sub{color:#444;font-size:10pt}.hdr{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10pt;margin:12pt 0;font:10pt ui-sans-serif,system-ui,sans-serif}
.hdr div{border-bottom:1pt solid #999;padding:14pt 0 2pt}
.box{border:1pt solid #bbb;border-radius:6pt;padding:8pt 10pt;margin:8pt 0;font-size:10pt}
.q{break-inside:avoid;margin:12pt 0}.qh{font:700 10pt ui-sans-serif,system-ui,sans-serif;color:#333;margin-bottom:3pt}
.opt{display:flex;gap:8pt;margin:3pt 0 3pt 6pt}.bub{flex:none;width:13pt;height:13pt;border:1pt solid #333;border-radius:50%;font:8pt/12pt ui-sans-serif,sans-serif;text-align:center}
.lines{margin-top:6pt}.lines div{border-bottom:.6pt solid #aaa;height:20pt}
code{font-family:ui-monospace,Menlo,monospace;font-size:.92em}
table{border-collapse:collapse;width:100%;font-size:9.5pt;margin:6pt 0}td,th{border:.6pt solid #bbb;padding:4pt 6pt;text-align:left;vertical-align:top}
th{background:#f2f2f2}.ok{color:#15803d;font-weight:700}.pa{color:#b45309;font-weight:700}.bad{color:#b91c1c;font-weight:700}
.legend span{display:inline-block;margin-right:12pt}.sw{display:inline-block;width:9pt;height:9pt;border-radius:2pt;margin-right:3pt;vertical-align:-1pt}
.src{font-size:9pt;color:#333}.conf{font:9pt ui-sans-serif,system-ui,sans-serif;color:#444;margin-top:5pt;display:flex;gap:5pt;align-items:center}.key{font:700 10pt ui-sans-serif,system-ui,sans-serif;color:#15803d}
"""


def _header(meta: dict, kind: str) -> str:
    prof = meta.get("professor") or {}
    tl = meta.get("time_limit_minutes")
    return (f"<h1>{html.escape(meta.get('title', 'Exam'))}{' · Answer key' if kind == 'key' else ''}</h1>"
            f"<div class='sub'>{html.escape(meta.get('series', ''))}{' #' + str(meta['number']) if meta.get('number') else ''}"
            f" · {html.escape(meta.get('field', ''))} · {html.escape(meta.get('level', ''))} · {html.escape(meta.get('date', ''))}"
            f" · Examiner: {html.escape(prof.get('name', ''))}"
            f" · {'Time limit: ' + str(tl) + ' min' if tl else 'Untimed'}</div>")


def render_paper(exam: dict) -> str:
    meta, qs = exam["meta"], exam["questions"]
    total = sum(q["points"] for q in qs)
    out = [f"<title>{html.escape(meta.get('title', 'Exam'))} (paper)</title><style>{PRINT_CSS}</style>", _header(meta, "paper"),
           "<div class='hdr'><div>Name</div><div>Date</div><div>Score&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/ " + f"{total:g}</div></div>"]
    instr = meta.get("instructions") or ""
    out.append(f"<div class='box'>{_md(instr)}<br>Reasoning questions are graded on the quality of the argument; "
               "a well-defended answer that differs from the key can earn full credit.</div>")
    lines = {"short": 10, "long": 30}
    sections = [("mc", "Part A: Multiple choice"), ("short", "Part B: Short reasoning"), ("long", "Part C: Long reasoning")]
    n = 0
    for t, name in sections:
        sq = [q for q in paper_order(qs) if q["type"] == t]
        if not sq:
            continue
        out.append(f"<h2>{name} ({sum(q['points'] for q in sq):g} pts)</h2>")
        for q in sq:
            n += 1
            extra = f" · {html.escape(q['expected_length'])}" if q.get("expected_length") else ""
            out.append(f"<div class='q'><div class='qh'>Q{n} · {q['points']:g} pt{'s' if q['points'] != 1 else ''}{extra}</div>{_md(q['prompt'])}")
            if t == "mc":
                for o in q["options"]:
                    out.append(f"<div class='opt'><span class='bub'>{html.escape(o['id'])}</span><span>{_md(o['text'])}</span></div>")
            else:
                out.append("<div class='lines'>" + "<div></div>" * int(q.get("answer_lines") or lines[t]) + "</div>")
            out.append("<div class='conf'>Confidence: <span class='bub'>G</span> guess <span class='bub'>U</span> unsure <span class='bub'>S</span> sure</div></div>")
    return standalone("".join(out))


def paper_order(qs: list) -> list:
    """Questions in the order the paper prints them (by section), so paper and key numbers match."""
    rank = {"mc": 0, "short": 1, "long": 2}
    return sorted(qs, key=lambda q: rank[q["type"]])


def render_key(exam: dict) -> str:
    meta, qs = exam["meta"], paper_order(exam["questions"])
    out = [f"<title>{html.escape(meta.get('title', 'Exam'))} (key)</title><style>{PRINT_CSS}</style>", _header(meta, "key")]
    out.append("<div class='box legend'><strong>Self-grading legend:</strong> "
               "<span><i class='sw' style='background:#15803d'></i><b class='ok'>✓ Correct</b>: full points</span>"
               "<span><i class='sw' style='background:#b45309'></i><b class='pa'>½ Partial</b>: some rubric points</span>"
               "<span><i class='sw' style='background:#b91c1c'></i><b class='bad'>✗ Incorrect</b>: 0 points</span></div>")
    # score sheet
    out.append("<h2>Score sheet</h2><table><tr><th>Q</th><th>Type</th><th>Concept</th><th>Objective</th><th>Points</th><th>Earned</th><th>✓ / ½ / ✗</th><th>G/U/S</th></tr>")
    for i, q in enumerate(qs, 1):
        out.append(f"<tr><td>{i}</td><td>{q['type']}</td><td>{html.escape(q.get('concept', ''))}</td><td>{html.escape(q.get('objective', ''))}</td><td>{q['points']:g}</td><td></td><td></td><td></td></tr>")
    out.append(f"<tr><th colspan=4>Total</th><th>{sum(q['points'] for q in qs):g}</th><th></th><th></th><th></th></tr></table>")
    out.append("<p class='src'>When you've graded it, give Claude the Earned and G/U/S columns (or a photo of this page) so the next exam can plan spaced review and target confident errors (S + ✗).</p>")
    out.append("<h2>Answers, rubrics and sources</h2>")
    for i, q in enumerate(qs, 1):
        out.append(f"<div class='q'><div class='qh'>Q{i} · {q['type']} · {q['points']:g} pt{'s' if q['points'] != 1 else ''}</div>{_md(q['prompt'])}")
        if q["type"] == "mc":
            ans = next((o for o in q["options"] if o["id"] == q["answer"]), {})
            out.append(f"<p class='key'>Answer: {html.escape(q['answer'])}. {_md(ans.get('text', ''))}</p><p>{_md(q.get('explanation', ''))}</p>")
            dn = q.get("distractor_notes") or {}
            if dn:
                out.append("<ul>" + "".join(f"<li><b>{html.escape(k)}</b>: {_md(v)}</li>" for k, v in dn.items()) + "</ul>")
        else:
            out.append("<table><tr><th>Criterion</th><th>Pts</th><th>What earns it</th></tr>" + "".join(
                f"<tr><td>{html.escape(r['criterion'])}</td><td>{r['points']:g}</td><td>{_md(r.get('description', ''))}</td></tr>" for r in q["rubric"]) + "</table>")
            out.append(f"<p><b>Reference answer:</b> {_md(q.get('model_answer', ''))}</p>")
            if q.get("alternatives"):
                out.append(f"<p><b>Other valid approaches:</b> {_md(q['alternatives'])}</p>")
        if q.get("sources"):
            out.append("<div class='src'><b>Sources:</b><ol>" + "".join(
                f"<li>{html.escape(s['title'])}{(' · ' + html.escape(s['url'])) if s.get('url') else ''}{(' · ' + html.escape(s['note'])) if s.get('note') else ''}</li>"
                for s in q["sources"]) + "</ol></div>")
        out.append("</div>")
    if exam.get("review_note"):
        out.append(f"<h2>Examiner's review note</h2><p>{_md(exam['review_note'])}</p>")
    return standalone("".join(out))


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright  # optional dependency
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(html_path.resolve().as_uri())
        pg.pdf(path=str(pdf_path), format="Letter", print_background=True,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exam_json")
    ap.add_argument("--out", default="exam-out")
    ap.add_argument("--pdf", action="store_true", help="also write paper.pdf and key.pdf (needs playwright)")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--syllabus", help="syllabus.json: check every question maps to an objective and current-unit coverage")
    a = ap.parse_args(argv)

    try:
        exam = json.loads(Path(a.exam_json).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read {a.exam_json}: {e}", file=sys.stderr)
        return 1
    syllabus = None
    if a.syllabus:
        try:
            syllabus = json.loads(Path(a.syllabus).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: cannot read {a.syllabus}: {e}", file=sys.stderr)
            return 1
    errors, warnings = validate(exam, syllabus)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} error(s); fix them and rebuild.", file=sys.stderr)
        return 1
    print(f"OK: {len(exam['questions'])} questions, {sum(q['points'] for q in exam['questions']):g} points, {len(warnings)} warning(s)")
    if a.check:
        return 0

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frag = render_interactive(exam)
    (out / "exam.artifact.html").write_text(frag, encoding="utf-8")
    (out / "exam.html").write_text(standalone(frag), encoding="utf-8")
    (out / "paper.html").write_text(render_paper(exam), encoding="utf-8")
    (out / "key.html").write_text(render_key(exam), encoding="utf-8")
    written = ["exam.artifact.html", "exam.html", "paper.html", "key.html"]
    if a.pdf:
        try:
            to_pdf(out / "paper.html", out / "paper.pdf")
            to_pdf(out / "key.html", out / "key.pdf")
            written += ["paper.pdf", "key.pdf"]
        except Exception as e:  # noqa: BLE001
            print(f"warning: PDF export skipped ({e}). Open paper.html / key.html and print to PDF instead.")
    print("wrote: " + ", ".join(str(out / w) for w in written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
