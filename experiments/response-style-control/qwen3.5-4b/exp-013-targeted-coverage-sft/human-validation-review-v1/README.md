# Completed original A/C/D human review

User explicitly continued the original queue, not v2. All20 records have one
submitted response, exported read-only. Snapshot digest is in summary.json.
Original labels/full notes preserved; no annotations or frozen targets changed.

| Arm | Recipe | Pass | Partial | Fail | Sole preference |
| --- | --- | ---: | ---: | ---: | ---: |
| A / exp011 | Original80,4epochs | 9 | 6 | 5 | 3 |
| C / exp013 | 68original+12reviewed replacements,4epochs | 11 | 5 | 4 | 3 |
| D / exp014 | Exact C data,6epochs | 10 | 5 | 5 | 3 |

Preferences:9 ties,2 neither,3 each A/C/D. Notes identify me-020 A=D>C
and me-029 C=D. Seven generic ties remain unresolved; equal substance labels
do NOT prove equal preference. me-060 selected C but note says A=C>D;
retain C as primary and flag discrepancy, without requiring reannotation.
me-069 structured A=partial but prose says A=pass; structured primary retained.
Optional issue labels were not selected; empty arrays do not prove no issues.
Notes are submitted rationale, not independent assistant adjudication or
necessarily independently authored human reasoning.

Predeclared high-signal8: A2pass/5partial/1fail; C3/3/2; D2/4/2.
Without disputed me-089: all19 A9/5/5,C11/5/3,D10/4/5; anchors7 A2/4/1,
C3/3/1,D2/3/2. The recommendation does not depend on me-089.

## Agent interpretation, distinct from submitted ratings

C vs A crosses to pass on029/069/079, but059 moves pass to partial.029's
A answer selects the right product but is a sentence; the gain includes
answer-only compliance, not new factual knowledge.079 C selects the requested
rule family without unnecessary speculation about missing details.069 C helps
bounded causality but still has awkward Turkish and lacks concrete verification.
This is a small targeted improvement, not a general reasoning success.

D vs C crosses to pass on059/070, but069/079/090 move away from pass.
049 improves fail to partial.050 degrades partial to fail:619tokens, repetition,
contradictions and poor layout/desk recommendation.090 loses the user's explicit
request to just talk, replacing listening space with generic reassurance.
Both grammar items009/010 fail for all arms. No arm fully passes049/050.
C089 fails and A/D are partial, but its frozen reference is disputed.

C total1030 output tokens (median22,max188); D1569 (median37,max619),
52.3% more tokens. All nativeEOS: technical stopping succeeds while semantic
repetition remains. Lower D training loss is not better reasoning evidence.
Greater D length is partly driven by050, not proof of global verbosity growth.

Conclusion: narrow C intervention partly helps; longer D cosine recipe is not
a consistent improvement. Retain A as established comparison and C as candidate,
without declaring a globally superior model or promoting D. Next priority is
independently sourced training coverage for coherent mechanisms, trade-offs,
grammar and appropriate interaction; no validation paraphrases. Do not blindly
extend epochs or simultaneously raise rank/LR/batch. New experiments/data need
a separate approved plan; none launched here.

Limitations: repeated20 development questions, one seed/reviewer, non-blind,
ambiguous ties, structured/prose discrepancies. Not independent final accuracy
or statistically established superiority. Historical A/B ratings must not be
silently substituted for A's current three-way-context ratings.
