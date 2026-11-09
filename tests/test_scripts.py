"""Unit tests for the exam-coach scripts. Run: python -m unittest discover tests"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "exam-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_exam  # noqa: E402
import plan_next  # noqa: E402

SAMPLE = json.loads((ROOT / "examples" / "sample-exam.json").read_text())
HISTORY = json.loads((ROOT / "examples" / "sample-history.json").read_text())
SYLLABUS = json.loads((ROOT / "examples" / "sample-syllabus.json").read_text())


class TestValidate(unittest.TestCase):
    def test_sample_is_clean(self):
        errors, warnings = build_exam.validate(SAMPLE)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_sample_aligns_with_syllabus(self):
        errors, warnings = build_exam.validate(SAMPLE, SYLLABUS)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_unknown_objective_and_future_unit(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"][0]["objective"] = "U9.9"
        ex["questions"][4]["kind"] = "new"  # U3 objective before U3 is taught
        errors, warnings = build_exam.validate(ex, SYLLABUS)
        self.assertTrue(any("not in the syllabus" in e for e in errors))
        self.assertTrue(any("taught after" in w for w in warnings))

    def test_missing_distractor_note_is_error(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"][0]["distractor_notes"].pop("B")
        errors, _ = build_exam.validate(ex)
        self.assertTrue(any("distractor_notes missing" in e for e in errors))

    def test_easy_exam_warns(self):
        ex = copy.deepcopy(SAMPLE)
        for q in ex["questions"]:
            q["bloom"], q["difficulty"], q["kind"] = "understand", 1, "new"
        _, warnings = build_exam.validate(ex)
        self.assertTrue(any("too easy" in w for w in warnings))
        self.assertTrue(any("mean difficulty" in w for w in warnings))

    def test_bad_answer_key(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"][0]["answer"] = "Z"
        errors, _ = build_exam.validate(ex)
        self.assertTrue(any("not one of the option ids" in e for e in errors))

    def test_rubric_sum(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"][5]["rubric"][0]["points"] = 3
        errors, _ = build_exam.validate(ex)
        self.assertTrue(any("must add up" in e for e in errors))

    def test_unbalanced_and_blocked_warnings(self):
        ex = copy.deepcopy(SAMPLE)
        mc = ex["questions"][0]
        ex["questions"] = [dict(copy.deepcopy(mc), id=f"m{i}") for i in range(8)]
        _, warnings = build_exam.validate(ex)
        self.assertTrue(any("unbalanced" in w for w in warnings))
        self.assertTrue(any("interleave" in w for w in warnings))

    def test_script_injection_is_neutralised(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"][0]["prompt"] = "</script><script>alert(1)</script>"
        html = build_exam.render_interactive(ex)
        self.assertNotIn("</script><script>alert(1)", html)


class TestBuildCLI(unittest.TestCase):
    def test_builds_all_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(SCRIPTS / "build_exam.py"), str(ROOT / "examples" / "sample-exam.json"), "--out", d],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("exam.artifact.html", "exam.html", "paper.html", "key.html"):
                self.assertTrue((Path(d) / f).stat().st_size > 1000, f)
            frag = (Path(d) / "exam.artifact.html").read_text()
            self.assertFalse(frag.lower().startswith("<!doctype"))
            self.assertNotIn("__EXAM_JSON__", frag)
            paper = (Path(d) / "paper.html").read_text()
            self.assertNotIn("Solenoid field\"", paper)  # no answer data in the paper
            self.assertNotIn("n = 400 / 0.20 m", paper)

    def test_check_fails_on_invalid(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"meta": {}, "questions": []}, f)
        r = subprocess.run([sys.executable, str(SCRIPTS / "build_exam.py"), f.name, "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)


class TestPrint(unittest.TestCase):
    def test_key_numbering_matches_paper(self):
        ex = copy.deepcopy(SAMPLE)
        ex["questions"] = [ex["questions"][5]] + ex["questions"][:5]  # reasoning item first in file order
        paper, key = build_exam.render_paper(ex), build_exam.render_key(ex)
        first_paper = paper.split("Q1 ·")[1][:300]
        first_key = key.split("Q1 ·")[1][:300]
        self.assertIn("400 turns", first_paper)
        self.assertIn("400 turns", first_key)
        self.assertIn("G/U/S", key)
        self.assertIn("Confidence:", paper)


class TestPlanNext(unittest.TestCase):
    def test_syllabus_path(self):
        p = plan_next.plan({}, date(2026, 11, 6), 10, 0.9, SYLLABUS)
        lp = p["learning_path"]
        self.assertEqual(lp["current_unit"]["id"], "U2")
        self.assertEqual(lp["n_pretest"], 1)
        self.assertEqual(lp["pretest_objective"][0]["objective"], "U3.1")
        self.assertIn("U4", lp["out_of_scope_units"])
        self.assertEqual(lp["new_objectives"][0]["unit"], "U2")

    def test_hint_weakens_evidence(self):
        h = [{"date": "2026-11-01", "items": [{"concept": "x", "earned": 1, "points": 1, "hint_used": True}]}]
        c = plan_next.build_model(h)["x"]
        self.assertEqual(c.streak, 0)


    def test_forgetting_curve_anchor(self):
        self.assertAlmostEqual(plan_next.retrievability(10, 10), 0.9, places=3)
        self.assertAlmostEqual(plan_next.interval_for(10, 0.9), 10, places=3)

    def test_plan_prioritises_confident_errors(self):
        p = plan_next.plan(plan_next.build_model(HISTORY), date(2026, 11, 6), 12, 0.9)
        self.assertIn("Magnetic force", p["confident_errors_first"])
        self.assertEqual(p["review_concepts"][0], "Magnetic force")
        b = p["blueprint"]
        self.assertEqual(b["review"] + b["new"] + b["transfer"], 12)

    def test_empty_history_is_all_new(self):
        p = plan_next.plan({}, date(2026, 11, 6), 10, 0.9)
        self.assertEqual(p["blueprint"]["new"], 10)

    def test_mastery_needs_three_spaced_successes(self):
        c = plan_next.Concept("x")
        for d in (date(2026, 1, 1), date(2026, 1, 8), date(2026, 1, 30), date(2026, 3, 15)):
            c.update(d, 1.0, False)
        self.assertGreaterEqual(c.streak, 3)
        self.assertTrue(c.mastered())
        c.update(date(2026, 3, 16), 0.0, True)
        self.assertFalse(c.mastered())


if __name__ == "__main__":
    unittest.main()
