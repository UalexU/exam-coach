#!/usr/bin/env python3
"""Plan the next exam from past results (the learner model).

Reads a history file: a JSON list of result records, one per exam taken. Each
record is what the interactive page saves ("Copy results for next exam", or the
`results` rows in the artifact database):

  {"date": "2026-11-09", "number": 4, "score": 21.5, "total": 30, "reflection": "...",
   "items": [{"concept": "SNR scaling", "type": "mc", "kind": "review", "bloom": "apply",
              "earned": 1, "points": 1, "status": "ok", "confidence": "sure"}, ...]}

For each concept it keeps a small memory model inspired by FSRS (the scheduler
in Anki): stability S (days until recall probability drops to 90%), difficulty
D (1-10), and retrievability R = (1 + 19/81 * t/S) ** -0.5, which is 0.9 at
t = S. A concept counts as mastered after three spaced successful sessions with
S >= 21 days (successive relearning). The output is a blueprint for the next
exam: which concepts to review, how many new ones, which to use for transfer,
the target difficulty, and the confident errors to revisit first.

With --syllabus, the plan follows the course's learning path: new items come
from the core objectives of the unit being taught now (then any earlier
objectives never tested), one low-stakes pretest item previews the next unit,
and nothing from later units is examined for credit.

Usage:
  python plan_next.py history.json [--syllabus syllabus.json] [--today YYYY-MM-DD]
                      [--questions 14] [--target-retention 0.9] [--json]
  (pass "-" or a missing file as history for a first exam)
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from datetime import date

F, C = 19 / 81, -0.5  # FSRS-4.5 power forgetting curve: R = (1 + F*t/S)^C, R(S) = 0.9


def retrievability(t_days: float, s: float) -> float:
    return (1 + F * max(t_days, 0) / max(s, 0.1)) ** C


def interval_for(s: float, r_target: float) -> float:
    """Days until R falls to r_target."""
    return s / F * (r_target ** (1 / C) - 1)


@dataclass
class Concept:
    name: str
    s: float = 0.0          # stability in days (0 = never seen)
    d: float = 5.0          # difficulty 1..10
    last: str | None = None
    sessions: int = 0
    streak: int = 0         # consecutive successful sessions
    lapses: int = 0
    last_score: float = 0.0
    confident_errors: int = 0
    history: list = field(default_factory=list)

    def update(self, when: date, frac: float, conf_error: bool) -> None:
        """frac = share of points earned on this concept in one session (0..1)."""
        if self.s == 0:  # first exposure
            self.s = 0.6 + 4.0 * frac            # roughly FSRS initial stabilities: ~0.6 d (fail) .. ~4.6 d (easy)
            self.d = min(10, max(1, 7 - 4 * frac))
        else:
            t = (when - date.fromisoformat(self.last)).days
            r = retrievability(t, self.s)
            # difficulty drifts toward how hard it was this time
            self.d = min(10, max(1, self.d + 1.2 * (0.7 - frac)))
            if frac >= 0.8:      # success: bigger gain when recall was harder (low R) and the concept is easier
                gain = math.exp(1.0) * (11 - self.d) * self.s ** -0.2 * (math.exp(1.2 * (1 - r)) - 1)
                self.s = self.s * (1 + max(gain, 0.15))
            elif frac >= 0.4:    # partial: hold roughly steady
                self.s = max(0.6, self.s * 1.1)
            else:                # lapse
                self.s = max(0.5, min(self.s * 0.35, 2.0 + self.s * 0.1))
                self.lapses += 1
        self.streak = self.streak + 1 if frac >= 0.8 else 0
        self.sessions += 1
        self.last_score = frac
        self.last = when.isoformat()
        self.confident_errors += int(conf_error)
        self.history.append({"date": self.last, "score": round(frac, 2), "S": round(self.s, 1)})

    def mastered(self) -> bool:
        return self.streak >= 3 and self.s >= 21


def build_model(history: list[dict]) -> dict[str, Concept]:
    model: dict[str, Concept] = {}
    for rec in sorted(history, key=lambda r: (r.get("date") or "", r.get("number") or 0)):
        when = date.fromisoformat((rec.get("date") or date.today().isoformat())[:10])
        per: dict[str, list] = {}
        for it in rec.get("items", []):
            name = (it.get("concept") or "").strip()
            if not name or it.get("earned") is None or not it.get("points"):
                continue
            g = per.setdefault(name, [0.0, 0.0, False])
            # a correct answer reached with a hint is weaker evidence of recall
            g[0] += it["earned"] * (0.75 if it.get("hint_used") else 1.0)
            g[1] += it["points"]
            if it.get("confidence") == "sure" and it["earned"] < 0.5 * it["points"]:
                g[2] = True
        for name, (e, p, ce) in per.items():
            model.setdefault(name, Concept(name)).update(when, e / p, ce)
    return model


def syllabus_path(syllabus: dict, today: date, model: dict) -> dict:
    """Where the learner is on the course's learning path."""
    t = today.isoformat()
    units = syllabus.get("units", [])
    taught = [u for u in units if (u.get("start") or "") <= t]
    current = next((u for u in units if (u.get("start") or "") <= t <= (u.get("end") or "9999")), taught[-1] if taught else None)
    upcoming = next((u for u in units if (u.get("start") or "") > t), None)
    seen = {k.lower() for k in model}

    def objs(u, only_untested=True):
        out = []
        for o in u.get("objectives", []):
            if o.get("importance", "core") != "core":
                continue
            if only_untested and (o.get("concept") or "").lower() in seen:
                continue
            out.append({"objective": o["id"], "concept": o.get("concept", ""), "text": o.get("text", ""), "unit": u.get("id")})
        return out

    current_new = objs(current) if current else []
    backlog = [o for u in taught if u is not current for o in objs(u)]
    return {
        "current_unit": current and {"id": current.get("id"), "title": current.get("title")},
        "next_unit": upcoming and {"id": upcoming.get("id"), "title": upcoming.get("title"), "starts": upcoming.get("start")},
        "new_objectives": current_new + backlog,
        "pretest_objective": (objs(upcoming, False)[:1] if upcoming else []),
        "out_of_scope_units": [u.get("id") for u in units if (u.get("start") or "") > t],
        "objective_for_concept": {(o.get("concept") or "").lower(): o["id"] for u in units for o in u.get("objectives", [])},
    }


def plan(model: dict[str, Concept], today: date, n_questions: int, r_target: float, syllabus: dict | None = None) -> dict:
    rows = []
    for c in model.values():
        t = (today - date.fromisoformat(c.last)).days
        r = retrievability(t, c.s)
        rows.append({
            "concept": c.name, "R": round(r, 2), "stability_days": round(c.s, 1), "difficulty": round(c.d, 1),
            "days_since": t, "sessions": c.sessions, "streak": c.streak, "lapses": c.lapses,
            "confident_errors": c.confident_errors, "mastered": c.mastered(),
            "due": r < r_target or c.last_score < 0.8,
            "next_due_in_days": round(interval_for(c.s, r_target) - t, 1),
        })
    due = sorted([r for r in rows if r["due"] and not r["mastered"]],
                 key=lambda r: (-r["confident_errors"], r["R"], -r["difficulty"]))
    mastered = [r for r in rows if r["mastered"]]
    stable = sorted([r for r in rows if not r["due"] and not r["mastered"]], key=lambda r: r["R"])

    # blueprint: ~55% spaced review, ~30% new material, ~15% transfer/interleaving from strong concepts
    n_review = min(len(due), round(n_questions * 0.55)) if due else 0
    n_transfer = min(len(mastered) + len(stable), max(1, round(n_questions * 0.15))) if (mastered or stable) else 0
    n_new = max(0, n_questions - n_review - n_transfer)
    if not model:
        n_new, n_review, n_transfer = n_questions, 0, 0

    # aim for ~85% expected success: recent performance well above target -> harder items, below -> easier
    recent = [c.last_score for c in model.values()]
    avg = sum(recent) / len(recent) if recent else None
    if avg is None:
        difficulty = "calibrate: start at difficulty 3-4 (apply/analyze) with one stretch item"
    elif avg > 0.85:
        difficulty = "raise: harder scenarios, subtler near-miss distractors, more evaluate/create items"
    elif avg < 0.65:
        difficulty = "ease slightly: keep apply/analyze level but add hints and one-step-shorter scenarios"
    else:
        difficulty = "hold: the learner is in the productive 65-85% range"

    path = syllabus_path(syllabus, today, model) if syllabus else None
    if path:
        n_pre = 1 if path["pretest_objective"] and n_questions >= 8 else 0
        n_new = max(0, n_new - n_pre)
        path["n_pretest"] = n_pre
        objmap = path.pop("objective_for_concept")
        for r in rows:
            r["objective"] = objmap.get(r["concept"].lower(), "")

    return {
        "learning_path": path,
        "today": today.isoformat(),
        "average_recent_score": None if avg is None else round(avg, 2),
        "difficulty_adjustment": difficulty,
        "blueprint": {"review": n_review, "new": n_new, "transfer": n_transfer, "total": n_questions},
        "review_concepts": [r["concept"] for r in due[:n_review]] if n_review else [],
        "confident_errors_first": [r["concept"] for r in due if r["confident_errors"]],
        "transfer_candidates": [r["concept"] for r in (mastered + stable)][: max(n_transfer, 0)],
        "mastered": [r["concept"] for r in mastered],
        "concepts": sorted(rows, key=lambda r: r["R"]),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("history_json")
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--questions", type=int, default=14)
    ap.add_argument("--target-retention", type=float, default=0.9)
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON only")
    ap.add_argument("--syllabus", help="syllabus.json: follow the course's learning path")
    a = ap.parse_args(argv)
    raw = []
    if a.history_json != "-":
        try:
            raw = json.loads(open(a.history_json, encoding="utf-8").read())
        except FileNotFoundError:
            raw = []
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: cannot read {a.history_json}: {e}", file=sys.stderr)
            return 1
    history = raw if isinstance(raw, list) else raw.get("results", [raw])
    syllabus = None
    if a.syllabus:
        try:
            syllabus = json.loads(open(a.syllabus, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: cannot read {a.syllabus}: {e}", file=sys.stderr)
            return 1
    p = plan(build_model(history), date.fromisoformat(a.today), a.questions, a.target_retention, syllabus)
    if a.json:
        print(json.dumps(p, indent=2))
        return 0
    b = p["blueprint"]
    print(f"Next exam ({p['today']}): {b['total']} questions = {b['review']} spaced review + {b['new']} new + {b['transfer']} transfer")
    print(f"Difficulty: {p['difficulty_adjustment']} (recent avg {p['average_recent_score']})")
    lp = p.get("learning_path")
    if lp:
        cu, nu = lp["current_unit"], lp["next_unit"]
        print(f"Learning path: now in {cu['id'] + ' ' + cu['title'] if cu else 'n/a'}; next {nu['id'] + ' ' + nu['title'] + ' (' + nu['starts'] + ')' if nu else 'none'}")
        if lp["new_objectives"]:
            print("New items should test: " + "; ".join(f"{o['objective']} {o['concept']}" for o in lp["new_objectives"]))
        if lp["n_pretest"]:
            o = lp["pretest_objective"][0]
            print(f"1 pretest (low-stakes preview): {o['objective']} {o['concept']}")
        if lp["out_of_scope_units"]:
            print("Not yet taught (no credit items): " + ", ".join(lp["out_of_scope_units"]))
    if p["confident_errors_first"]:
        print("Confident errors to fix first: " + ", ".join(p["confident_errors_first"]))
    if p["review_concepts"]:
        print("Review: " + ", ".join(p["review_concepts"]))
    if p["transfer_candidates"]:
        print("Use in transfer/interleaved items: " + ", ".join(p["transfer_candidates"]))
    if p["mastered"]:
        print("Mastered (3 spaced successes): " + ", ".join(p["mastered"]))
    print("\nconcept                          R     S(d)  D    last  streak")
    for r in p["concepts"]:
        print(f"{r['concept'][:32]:32} {r['R']:.2f}  {r['stability_days']:5.1f} {r['difficulty']:4.1f} {r['days_since']:4}d  {r['streak']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
