PY ?= python3
SKILL = skills/exam-coach

.PHONY: test test-ui validate example package clean

test:            ## unit tests (stdlib only)
	$(PY) -m unittest discover tests -v

test-ui:         ## end-to-end browser test (needs playwright + chromium)
	$(PY) tests/ui_test.py

validate:        ## validate the example exam against the example syllabus
	$(PY) $(SKILL)/scripts/build_exam.py examples/sample-exam.json --check --syllabus examples/sample-syllabus.json

example:         ## build the example exam into exam-out/
	$(PY) $(SKILL)/scripts/build_exam.py examples/sample-exam.json --out exam-out --syllabus examples/sample-syllabus.json --pdf
	$(PY) $(SKILL)/scripts/plan_next.py examples/sample-history.json --syllabus examples/sample-syllabus.json --today 2026-11-06

package:         ## build dist/exam-coach.skill (zip) for upload to Claude
	mkdir -p dist && cd skills && zip -qr ../dist/exam-coach.skill exam-coach -x 'exam-coach/evals/results/*' '*/__pycache__/*'
	@echo "dist/exam-coach.skill"

clean:
	rm -rf exam-out dist **/__pycache__
