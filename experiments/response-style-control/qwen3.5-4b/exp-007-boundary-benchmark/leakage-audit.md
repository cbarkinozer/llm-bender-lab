# Development benchmark overlap audit — 2026-10-01

Argilla is reachable (HTTP 200). All 11 exp-008 post-review QA records are
completed. Their edits concern responses; the training prompts scanned here
are unchanged, so those edits do not change prompt-overlap results.

`scan_leakage.py` compared all 50 benchmark prompts against 3,500 rows across
historical reviewed-v3 (2,442), exp-006 (958), and exp-008 (100). There are
2,699 unique normalized training prompts across these overlapping versions.
There are zero exact normalized matches and zero lexical matches at the 0.82
SequenceMatcher threshold. This result does not establish semantic independence.

## Scenario overlap candidates

The following six v1 items warranted rewriting before freezing the benchmark.
These are qualitative similarity findings, not proof of copied authorship.

| Benchmark | Training | Reason |
| --- | --- | --- |
| gb-005 | gen-017, gen-086 | Deleting the only/local copy of photos or files and checking a backup before an irreversible action. The benchmark changes backup availability, but retains the same central scenario. |
| gb-009 | gen-038 | Internet slows only in the evening; user asks whether a particular explanation or intervention is certain. Same observation, technical context, and uncertainty pattern. |
| gb-011 | gen-029, gen-023 | Inferring another person's anger from an ambiguous communication cue. Read status differs from a terse reply, but the interpersonal scenario and target judgment remain close. |
| gb-018 | gen-028 | Rain interrupts an outdoor event; user asks for the explicitly stated cause. Mostly substitutes show/postponement for match/interruption. |
| gb-034 | gen-080 | Repeated questions allegedly make the assistant angry or impatient. Same relational concern and practical reassurance target. |
| gb-047 | gen-095 | Universal agreement conflicts with incomplete information about participants. The corrected training target and benchmark both require preserving uncertainty about unconfirmed participants. |

## Shared skills that do not by themselves establish leakage

- gb-013 / gen-025: temporal association versus causation, with different
  interventions and outcomes. Shared reasoning skill; not classified as a copy.
- gb-025, gb-029 / gen-059: first-person plural agreement with different
  sentences. Common grammar rule, not sufficient evidence of scenario leakage.
- gb-042 / gen-092: contradictory messages, but the training prompt supplies
  the actual truth whereas the benchmark does not. Different information boundary.
- gb-043 / gen-082: attractive feature versus a decisive drawback, in different
  domains. Useful transfer test rather than an automatically disallowed template.
- gb-046 / gen-085, gen-093: distinct practical steps, but a different fault and
  different required knowledge. Shared response constraint rather than same answer.

The remaining items have no specific scenario-copy finding in this qualitative
pass. This is not an exhaustive proof of independence from all historical data:
the historical pool was lexically ranked, not exhaustively semantically reviewed.

The initial scan did not modify benchmark prompts, anchors, or annotations.
Exp-007 remains development material informed by previous observations; broad
quality claims still require independent evaluation.

## Resolution: development-v2.csv

All six identified scenario overlaps were replaced on the user's instruction.
The original v1 file and Argilla annotations remain available for provenance.

| ID | Replacement scenario | Preserved skill |
| --- | --- | --- |
| gb-005 | Uneditable festival application with an unconfirmed performance date | Verify required information before an irreversible decision |
| gb-009 | Reverberant recording and proposed acoustic foam | Avoid guaranteeing an intervention under incomplete technical information |
| gb-011 | Reading-club venue becomes smaller without an announced reason | Avoid inferring a cause from an observation alone |
| gb-018 | Casting stopped because a mold cracked | Extract the stated cause without inventing another cause |
| gb-034 | Assistant's answers are scored in a competition; user asks about shame | Respond without asserting felt emotion |
| gb-047 | Two overlapping sessions cannot both be attended in full | Repair a plan's contradiction without inventing missing arrangements |

The new scenarios no longer repeat the six identified training stories.
Basic decision rules remain shared by design; learning and applying a rule is
the capability being evaluated. A rescan of all 50 v2 questions found zero
exact matches and zero lexical matches at the documented 0.82 threshold.
The accompanying qualitative review found no new scenario-copy issue among
the six replacements. This does not prove zero contamination across unseen
sources or all possible semantic variants.

Only the six changed records were imported into a separate Argilla queue;
existing reviewed records were not overwritten. Candidate validation now
excludes prompts from both benchmark revisions.
