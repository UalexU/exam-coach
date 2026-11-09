"""End-to-end browser test of the interactive exam page (Playwright).
Run: python tests/ui_test.py [--shots DIR]"""
import subprocess, sys, tempfile, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument("--shots"); a = ap.parse_args()
out = Path(tempfile.mkdtemp())
subprocess.run([sys.executable, str(ROOT / "skills/exam-coach/scripts/build_exam.py"), str(ROOT / "examples/sample-exam.json"), "--out", str(out)], check=True, capture_output=True)
url = (out / "exam.html").as_uri()
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme, vw in (("light", 1100), ("dark", 390)):
        pg = b.new_page(viewport={"width": vw, "height": 900}, color_scheme=scheme)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(url)
        assert pg.locator("#start").is_visible(), "start screen"
        pg.screenshot(path=str(out / f"intro-{scheme}.png"), full_page=False)
        pg.click("#start")
        assert pg.locator("#timer").inner_text().startswith("29:") or pg.locator("#timer").inner_text().startswith("30:"), pg.locator("#timer").inner_text()
        # q1 correct+sure, q2 wrong+sure (confident error), q3 correct, q4 wrong, leave q5 blank, answer q6
        pg.click("#q-q1 .opt:has-text('2.7 MHz')"); pg.click("#q-q1 .conf button[data-k=sure]")
        pg.click("#q-q2 .opt:has-text('lengthens at low field')"); pg.click("#q-q2 .conf button[data-k=sure]")
        pg.click("#q-q3 .opt:has-text('Coil and preamp')")
        pg.click("#q-q4 .opt:has-text('~23')")
        pg.fill("#q-q6 textarea", "Signal goes as B0 squared; coil noise dominates so SNR ~ B0^(7/4).")
        assert "5/6" in pg.locator("#progtxt").inner_text()
        assert pg.locator("#q-q1 .hint-txt.hidden").count() == 1
        pg.click("#q-q1 .hint-btn"); assert pg.locator("#q-q1 .hint-txt.hidden").count() == 0
        pg.screenshot(path=str(out / f"exam-{scheme}.png"), full_page=False)
        pg.click("#submit"); pg.click("#submit")  # first click warns about the unanswered item
        pg.wait_for_selector(".score-ring")
        assert pg.locator("#r-q1.res.ok").count() == 1
        assert pg.locator("#r-q2.res.bad").count() == 1
        assert pg.locator("#r-q2 .hc").count() == 1, "confident error callout"
        assert pg.locator("#r-q5.res.bad").count() == 1, "blank MC is wrong"
        assert pg.locator("#r-q6.res.pending").count() == 1
        # self-grade q6: full on first criterion, half on second -> partial 3/4
        pg.click("#r-q6 .crit >> nth=0 >> button.f"); pg.click("#r-q6 .crit >> nth=1 >> button.h")
        assert pg.locator("#r-q6.res.partial").count() == 1
        assert "3 / 4" in pg.locator("#r-q6 .pts").inner_text()
        ring = pg.locator(".score-ring").inner_text()
        assert "5 / 9" in ring, ring  # q1 1 + q3 1 + q6 3
        assert pg.locator(".cal").count() == 1
        assert "used a hint" in pg.locator("#r-q1").inner_text()
        assert "objective U1.1" in pg.locator("#r-q1").inner_text()
        pg.screenshot(path=str(out / f"results-{scheme}.png"), full_page=True)
        # reload keeps state
        pg.reload(); pg.wait_for_selector(".score-ring")
        assert "5 / 9" in pg.locator(".score-ring").inner_text()
        pg.close()
    # auto-submit on expiry
    pg = b.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url); pg.fill("#tl", "5"); pg.click("#start")
    pg.evaluate("""() => { const k = Object.keys(localStorage)[0]; const s = JSON.parse(localStorage[k]); s.startedAt -= 6*60000; localStorage[k] = JSON.stringify(s); }""")
    pg.reload(); pg.wait_for_selector(".banner")
    assert "Time expired" in pg.locator(".banner").inner_text()
    b.close()
assert not errors, errors
if a.shots:
    import shutil; Path(a.shots).mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"): shutil.copy(f, a.shots)
print("UI test passed:", out)
