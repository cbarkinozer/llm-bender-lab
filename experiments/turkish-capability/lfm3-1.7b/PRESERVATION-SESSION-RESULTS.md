# Three-experiment results, 2026-11-19

All three authorized experiments completed. Two new LoRA runs,240 raw inference
outputs, and a16-question blinded Turkish review are available. All189 backup
manifest files and all four new adapters are verified locally; the pod can close.
See [backup receipt](PRESERVATION-BACKUP.json). No full weights were downloaded.

The new runs did not fix the arithmetic failure. SFT directly on the original
base also produces it, so CPT alone cannot explain the regression. Neither new
run is a demonstrated replacement for the existing bilingual69 candidate.
Owner review is complete; see [decoded findings](PRESERVATION-OWNER-REVIEW.md).
Exp013 leads relative preference but many answers are wrong; no successful
replacement is established. No publication was performed.

## Thinking diagnostic: same eight symbolic controls

| Candidate | Thinking off | Thinking on |
|---|---:|---:|
| Original LiquidAI base | 8/8 | 8/8 |
| CPT + Turkish60 SFT | 0/8 | 0/8 |
| CPT + bilingual69 SFT | 0/8 | 0/8 |
| Original base + bilingual69 SFT (exp012) | 1/8 | 1/8 |
| Original base + preservation69 SFT (exp013) | 1/8 | 1/8 |

Counts are required final numeric values, individually inspected. Old thinking-off
outputs are reused only for identical prompts/model/decoder. Original base thinks
before producing the correct result; SFT candidates immediately emit `</think>`
on the symbolic controls even when the native prefix opens thinking. New runs
terminate normally but mostly give wrong short answers. For example exp012 gives
165 for `144 / 12 + 9 * 8`, and exp013 also gives165; the answer is84.

This is a consumed diagnostic, not fresh general accuracy. It shows the current
SFT recipe can strongly impair this behavior without CPT. It does not isolate
the effects of empty-think supervision, concision, learning rate, individual bad
targets, or other training-distribution changes. It does not prove the underlying
capability is irreversibly erased. Removing CPT and toggling thinking did not
restore it in these runs.

Thinking was not ineffective on every task: Turkish60's tank problem changed
from12 to the correct33 minutes, and its ratio-share answer corrected reversed
largest/smallest roles. Bilingual69 also corrected those ratio roles. These
item-level gains are preserved in the paired16-task diagnostic; they do not
offset the unchanged symbolic0/8 or establish a general recovery.

## Fresh holdout: final numeric values

All70 numeric outputs were read, including apparent automatic matches. Correct
final values alone do NOT establish sound explanations, units, Turkish fluency,
or full task correctness. Some rows have explicit contradictory explanations.

| Candidate | Turkish numeric (7) | English numeric (7) | Fresh32 length-limit hits |
|---|---:|---:|---:|
| Original base | 3/7 | 7/7 | 4 |
| Turkish60 | 2/7 | 6/7 | 0 |
| bilingual69 | 1/7 | 6/7 | 0 |
| exp012 original-base bilingual | 1/7 | 5/7 | 0 |
| exp013 original-base preservation | 1/7 | 4/7 | 0 |

Of the correct-value Turkish outputs, contradiction/unit flags occur in3/3 for
base,1/2 for Turkish60,1/1 for bilingual69,0/1 for each new run. In English,
flags occur in3/6 for bilingual69 and1/5 for exp012. These are assistant review
flags, not independently adjudicated semantic scores; see the full per-item audit.
The eight logical/general tasks per language require separate meaning and
constraint judgments. In particular, answering 'No' to underdetermination while
giving impossible switch assignments is not treated as successful reasoning.

The last-number automatic screen undercounts LaTeX fractions, answers at the
beginning followed by numerical explanations, and answers with trailing numerical
unit exponents. Its diagnostic counts are NOT the table above. The preserved
manual audit supersedes that heuristic for final-value counts and records source
hashes. No outputs or owner judgments were edited.

The supplement did not improve held-out Turkish numeric results; English dropped
from5/7 to4/7 versus the matched original-base control. This tiny, correlated,
single-seed sample does not prove a population-level difference. It also does not
disprove retention mixing in general: the80 short rows supply only1.95% of all
supervised tokens, repeat five reasoning templates, and were combined with
original-row reweighting. Supplement and reweighting effects cannot be separated.

## Training and representation checks

Both new runs: original pinned BF16 LiquidAI base, independent fresh LoRA,
LR1e-4, rank32/alpha64, micro2/accum4, cosine113 updates/warmup6. Primary checkpoint69
was fixed before inference;113 retained as a backup, not selected on the new test.
32,210,944 trainable parameters. Total target exposure209811 versus209590;
at step69,125664 versus125642. All sequences fit4096; actual maximum1602 tokens.

Smoke, finite gradients, EOS/labels, save/reload, and tiny-overfit passed for both.
Tiny-overfit train NLL:2.8631→0.5206 (exp012),2.8631→0.5138 (exp013).
Actual SFT train runtimes75.54s and77.52s, mean training loss2.0324 and1.9519.
Lower loss in exp013 did not translate to improved held-out arithmetic.
All final adapters and inference merges passed exact save/reload probes.

The640 data has120 nonempty reasoning rows; the720 has160. All nonempty
`worked_solution` fields survived native rendering and supervision. Raw message/
reasoning scans found no `<think>`, `<thinking>`, `<REASONING>` or `<ANSWER>`
wrappers in either semantic training dataset. Native thinking tags are added by
the template. No masking change was made. This rules out accidentally dropping
all provided reasoning in these runs, but not learned preference for immediate
closure on direct-answer tasks. Some generated legacy-looking wrappers therefore
cannot simply be attributed to those literal wrappers in this training data.

Source/code/data hashes, execution fixes and limitations:
[frozen plan](PRESERVATION-SESSION-PLAN.md). Runtime Python3.11.17 differs from the
historical3.12 stack; pinned package and hardware manifests are preserved.
The within-session original-base versus its new SFT adapter comparison shares
the inference backend and generation settings. No broad causal CPT claim.

## Review and next decision

[Argilla:16 Turkish questions, four candidates](http://127.0.0.1:6900/dataset/636c2195-0f64-4131-97b5-1f44a1306768/annotation-mode).
Only ordering and reasoning; labels are randomized per record. References and
identity mapping remain hidden. English and arithmetic diagnostics are already
available locally; no need to annotate all240 generations.

Retain the existing bilingual69 as the current Turkish candidate until this review
establishes a better one. Do not scale translations or start DPO based on lower
training loss. If another training test is justified, investigate the SFT update
strength and reasoning/answer distribution with one controlled recipe change,
rather than assuming a thinking flag or more translated rows resolves the issue.
The current32 is consumed after this comparison; future tuning uses it as dev
and needs a fresh holdout for final claims.

A public research preview could disclose these limitations if the owner chooses,
but 'only a little arithmetic forgetting' is not supported by0–1/8 symbolic
results. A production-quality or no-catastrophic-forgetting claim is not established.
Publication and further GPU runs remain future decisions.

Local evidence directory: `preservation-session-v01-local/analysis/`, especially
`automatic-diagnostics.json`, [preserved manual arithmetic audit](PRESERVATION-ARITHMETIC-AUDIT.json),
`training-representation-summary.json`, and `fresh-review.csv`.
