# Writing hard, fair questions

The aim is for a learner who understands the concept to get the item right by reasoning, and for one who half-understands it to be pulled toward a specific, nameable wrong answer. Then the result tells you, and them, exactly what's missing.

## 1. Start from the objective, not the fact

Write the objective as a verb the learner must perform: *predict*, *derive*, *choose and justify*, *diagnose*, *critique*. Then ask: what would someone who truly has this skill do that someone who memorized the notes couldn't? Build the item around that difference.

| Weak (recall) | Strong (reasoning) |
|---|---|
| "What limits an electromagnet's field?" | "Your electromagnet has a 4 mm gap and a steel core. You need 20 % more field without more current. What do you change, and why?" |
| "What is R-hat?" | "Four chains give R-hat = 1.03 and bulk-ESS = 180 for τ. What's the justified next step?" |
| "Define a confounder" | "A study finds X predicts Y. Which added variable would most change the conclusion, and why?" |

## 2. Item patterns that force thinking

- **Predict the consequence** of a change (parameter, design, assumption).
- **Diagnose** a result: here's an output or symptom; what's the most likely cause?
- **Choose and justify** between approaches under explicit constraints.
- **Spot the flaw** in a claim, derivation or study design.
- **Transfer**: apply a mastered concept in an unfamiliar setting or combine two concepts.
- **Estimate**: an order-of-magnitude calculation where unit or scaling errors are the trap.
- **Two-step**: the item can only be answered by first working out an intermediate result.

## 3. Near-miss distractors

Write the key first, then build each wrong option from a specific failure of understanding. Good distractor sources:

| Type | Example flaw |
|---|---|
| **Documented misconception** | The belief the literature or teaching notes say students hold (reversed direction of an effect). |
| **Right reasoning, one slip** | Correct method, one step wrong: a unit conversion, a factor of 2, linear instead of quadratic scaling. |
| **True but irrelevant** | A correct statement that doesn't answer *this* question. |
| **Right under another assumption** | Correct in a different regime (below vs above saturation, large-n vs small-n). |
| **Over-generalisation** | A rule of thumb applied past its limits. |
| **Partial answer** | Names one of two required factors; looks complete at a glance. |

At least two of the three distractors should be of the first four types. A distractor nobody would choose adds nothing; replace it.

Record each flaw in `distractor_notes`. The explanation the learner sees is where the teaching happens.

## 4. Fairness rules (difficulty must come from the concept)

- One option is defensibly best given the stated assumptions; say which assumptions matter.
- Options are similar in length, grammar and specificity, so the key doesn't stand out.
- No "all/none of the above", no double negatives, no "which is NOT" unless the concept truly calls for it (and then bold **NOT**).
- Numbers are realistic and units explicit. Calculations are doable in the time allowed.
- The stem contains everything needed; no hidden context.

## 5. Reasoning questions

- Make the learner commit: "predict and justify", "choose and defend", "find the flaw and fix it".
- Rubric criteria name the *ideas* a strong answer must show, with points. Include one criterion for stating assumptions or limitations.
- `alternatives` lists other defensible lines of argument, so a creative but sound answer isn't penalised.
- `model_answer` is a strong answer, not the only acceptable one.

## 6. Calibrating difficulty (1-5)

| Level | Meaning |
|---|---|
| 1 | Recognition: right after studying, most learners get it (pretests only). |
| 2 | One-step application with clear cues. |
| 3 | Application in a new scenario, or two steps; one near-miss distractor. |
| 4 | Analysis or diagnosis; two near-miss distractors; assumptions matter. |
| 5 | Evaluation/synthesis across concepts; strong learners sometimes miss it. |

Aim for an average of 3-4, adjusted by the planner's difficulty signal (raise when recent scores are above 85%, ease when below 65%).

## 7. Hints

A hint is a question the professor would ask, not a fact: "Which noise source grows with frequency? Now go to the low-frequency end." It points to the line of reasoning. It never names or rules out an option.
