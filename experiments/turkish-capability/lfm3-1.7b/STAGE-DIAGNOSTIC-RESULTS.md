# Base -> CPT -> bilingual SFT: GPU diagnosis

Run completed 2026-11-19 UTC (2026-11-20 Istanbul). No training performed.
All 264 diagnostic outputs plus two smoke outputs are downloaded. The local
backup receipt verifies all 32 packaged files and controller completion.
Archive SHA256: `97445484f9c240b09aa53b47852dcc8109e8de7a839ec1c92bfa5ac5f7b0168e`.
No full weights were downloaded; the pod is safe to close.

Frozen protocol and model identities: [stage-diagnostic-v01](stage-diagnostic-v01/README.md).
Native prompt/EOT checks, pinned weight hashes, BF16 merge/save/reload checks
and smoke passed. All three stages used the same GPU/backend/decoding.

## Important scoring correction

The automatic symbolic screen looks for an integer at the END of the final
answer. It is not a semantic arithmetic score. Raw-output inspection of all
48 symbolic responses finds:

| Model | Thinking off: correct calculations present | Thinking on: correct final answer |
|---|---:|---:|
| Original base | 8/8 | 8/8 |
| CPT | 8/8 | 8/8 |
| CPT + bilingual checkpoint69 | 0/8 | 0/8 |

In thinking-off mode, CPT correctly computes every expression but appends
forum-like text, invented sources, examples or repetition. Consequently the
automatic terminal-number screen reports **0/8**, despite correct arithmetic
being present. That screen must NOT be described as proof that CPT forgot
these calculations. Base also explains calculations despite the number-only
instruction; calculation correctness and format compliance are separate.

In thinking-on mode, base and CPT both produce a nonempty reasoning section
and the correct bare final integer on all eight symbolic controls. Bilingual
SFT immediately emits `</think>` and the same wrong answers in both modes:
263, 276, 165, 43, 1, 169, 238, 177 (questions01 through08).
Expected: 259, 160, 84, 53, 35, 210, 38, 147.

Example01: CPT computes 54+38=92, 92*3=276, 276-17=259.
Bilingual SFT answers263. Turning thinking on does not change that answer.
These eight consumed controls locate an observed behavioral regression after
SFT; they do not establish permanent loss of the underlying capability.

## Stopping and thinking behavior

| Mode | Model | EOS | Token limit | Loop guard | Median generated tokens |
|---|---|---:|---:|---:|---:|
| Off,72 prompts | Base | 72 | 0 | 0 | 145.5 |
| Off,72 prompts | CPT | 36 | 33 | 3 | 406 |
| Off,72 prompts | CPT+bilingual69 | 72 | 0 | 0 | 50 |
| On,16 prompts | Base | 15 | 1 | 0 | 272.5 |
| On,16 prompts | CPT | 13 | 3 | 0 | 199.5 |
| On,16 prompts | CPT+bilingual69 | 16 | 0 | 0 | 21.5 |

Thinking-on: base has nonempty text before `</think>` in16/16 outputs, CPT
in8/16 (the symbolic controls), bilingual SFT in0/16. The eight CPT Turkish
word-problem outputs do not close their thinking section. EOS alone therefore
does not imply a usable final answer. SFT improves stopping here while losing
these symbolic answers and producing an immediate-answer policy.

## Interpretation and next decision

The evidence separates two issues: CPT shows severe continuation/stopping
problems, while this subsequent SFT shows a regression on symbolic arithmetic
and suppresses visible reasoning. We should not frame this as a demonstrated
unavoidable exchange of arithmetic for Turkish. Neither a causal mechanism nor
a general Turkish capability gain is established by these controls.

Prioritize an SFT target-policy experiment that preserves verified worked
solutions and native thinking behavior, with a matched control and supervised
token budget. Freeze the exact contrast after the remaining prose review;
do not change learning rate, data quantity and target policy together. Existing
blank-thinking examples are owner-intentional and should not be silently filled
or masked. No new training is authorized or started by this report.

## Review still required

The full264-output CSV is prepared locally at
`stage-diagnostic-v01-local/analysis/correctness-review.csv`; machine summary
at `analysis/diagnostics.json`. The symbolic subset above was inspected in full.
The prose subset still needs systematic adjudication of meaning, units,
contradictions, requested language and natural Turkish before publishing any
four-direction accuracy table or selecting a final training recipe. Initial
spot checks already show wrong units and contradictory answers; merely finding
the expected number would overstate quality.

Keep the12 seen-training probes per model separate from unseen-task results.
All previous evaluation questions are consumed diagnostic data, not a fresh
final holdout. No automatic overall winner and no new annotation task is claimed.

All raw outputs, token IDs, logs, environment, merge receipts and source hashes
remain in the verified ignored local artifact directory. An immutable Git
snapshot of all266 outputs (including smoke), their manifests, environment,
prompt audit, merge receipts, completion, controller log, backup receipt and
machine summary is also saved in [evidence](stage-diagnostic-v01/evidence/).
Its evidence-manifest records each copied file's SHA256 and byte count;
raw inference files were checked against the verified backup receipt.
The historical automatic summary is preserved unchanged: its terminal-number
screen must be interpreted with the manual correction above. Reference answers
remained local during inference.
