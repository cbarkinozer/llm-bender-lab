# Experiment journal and blog evidence trail

Updated: 2026-10-03. Owner request: preserve what we tried, results, failures,
fixes and decisions so a later blog can tell the complete story.
This is an evidence journal, not a claim that the project has already succeeded.
Append dated entries for every future round; preserve previous snapshots.

## What we are trying to improve

A useful Turkish assistant that answers directly, follows requested formats,
extracts the right fact/entity, summarizes faithfully, explains necessary
mechanisms without padding, clarifies only when needed, avoids unsupported
additions, respects Turkish morphology and near-word distinctions (including
doktor/doktora, veri/vergi and i/ı), and does not invent personal feelings,
memories or attachment. Neutral acknowledgment should remain natural and useful.

Plain prose is a preferred default, not an instruction to discard useful lists,
code or requested formatting. Correct reasoning and natural Turkish take
priority over removing every Markdown symbol. No finite evaluation establishes
zero hallucination. Keeping original answer wording is an editing strategy,
not evidence of protection against catastrophic forgetting.

## Historical trajectory

These entries distinguish completed artifacts from qualitative user impressions.
Earlier README statuses may describe an earlier stage; consult linked run notes.

| Experiment | What we tried | Observed outcome / decision |
| --- | --- | --- |
| exp003–005 | Early style-control SFT, cleaned core data, then targeted policy examples | Historical context and artifacts in the [registry](README.md); no retrospective accuracy numbers invented here |
| [exp006](exp-006-quality-repair-sft/README.md) | 958-row dataset, five reviewed quality-repair families; keep exp005 recipe | Training/generation completed. User later felt some overfitting, generalizability weakness and Turkish-quality loss; this is qualitative feedback, not a measured overfit diagnosis |
| [exp007](exp-007-boundary-benchmark/README.md) | New 50-item rules-and-exceptions development benchmark; replace overlapping scenarios | Development instrument, not training data or independent final test |
| [exp008](exp-008-generalization-sft/GPU-RUN-NOTES.md) | Standalone 100 corrected examples, three epochs, LR1e-4, rank16; 39 steps | Mean training loss1.941578596; 82.2506s. Initially questioned as too little data for the broader goal; user later liked Turkish quality but noticed a question-asking loop. Not a clean one-variable comparison with exp006 |
| [exp009](exp-009-minimal-edit/README.md) | New phase: fresh base, 100 curated questions split80/20, user-edited base answers, 80-row SFT; LR5e-5, two epochs/20steps | User rejected outputs as very weak: unwanted formatting, verbosity and broken Turkish persisted. “Underfit” describes the user's impression; low training loss or style alone cannot establish the mechanism |
| [exp010](exp-010-lr-ablation/GPU-RUN-NOTES.md) | Same80/20 and recipe, double LoRA LR to1e-4; two epochs/20steps | Mean training loss1.3649966836, 89.7461s. User saw slight shortening but little substantive improvement. Training completed; initial adapter inference, not training, hit a repetition loop |
| [exp011 / A](exp-011-duration-ablation/README.md) | Same reviewed80 targets, extend two epochs to four/40steps | Encouraging user preference on explanation and naturalness, but persistent shared failures; review below |
| [exp012 / B](exp-012-coverage-ablation/README.md) | Same four-epoch recipe as A, retain56 rows and replace24 with approved reasoning/grounded scenarios | Better precision on selected items; some explanation/naturalness/uncertainty regressions. Complementary, not a universal winner |

Old adapters were not continued into the new phase. A and B each started
independently from the pinned base. There is no adapter-merging result.

## Latest completed pair: reproducible intervention

Both: unsloth/Qwen3.5-4B revision
`3764fa359b9082ea5a1e4a5e3ac3aaf6e9671636`; BF16 LoRA rank/alpha16/16,
attention + MLP projections, LR1e-4, microbatch1, accumulation8,
effective batch8, max sequence1024, seed3407, AdamW8bit, cosine,
warmup2, no packing/replay, final-assistant-only labels including native EOS.
Empty non-thinking generation prefix is masked. Trainable parameters21,233,664.

| Recorded quantity | A / exp011 | B / exp012 |
| --- | --- | --- |
| Epochs / optimizer steps | 4 / 40 | 4 / 40 |
| Mean training loss | 1.1178216442465783 | 1.4069858700037003 |
| Training runtime seconds | 219.7631 | 128.5674 |
| Supervised tokens per epoch | 5384 | 6594 |
| Primary answers reaching native EOS | 20/20 | 20/20 |
| Median / maximum output tokens | 36 / 394 | 29 / 178 |
| W&B run | [93a090aa](https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/93a090aa) | [3f3844d7](https://wandb.ai/c-barkinozer/llm-bender-lab-response-style-control/runs/3f3844d7) |

Names: `exp011-sft-duration-80rows-4ep`,
`exp012-sft-coverage-80rows-4ep`. Future W&B names use informative
sft/eval descriptions, not the unhelpful “full” prefix.

Confounds: longer duration extends the cosine trajectory, not merely the
number of otherwise identical updates. B has +22.47% supervised-token exposure;
its loss is on different targets. A paid initial compilation overhead, so these
runtimes are not a clean throughput comparison. Neither loss nor shortness is
an accuracy score. One seed was run; uncertainty across seeds is unknown.

Primary inference used HF/Unsloth adapter reload, greedy decoding,
repetition penalty1.05, max4096 tokens, thinking off, no extra system prompt,
identical rendered input IDs/settings/desired references between A/B.
Repeat/time guards were enabled; none fired on these40 outputs. Historical base
answers came from vLLM, so backend/numerical parity with adapters is not exact.

## Human review frozen on 2026-10-03

Read-only [Argilla snapshot](exp-012-coverage-ablation/human-review-v1/argilla-snapshot.json)
preserves all20 prompts, desired/A/B answers, submitted responses, response IDs
and timestamps. No annotations were rewritten and no issue labels invented.

| User judgment | A | B |
| --- | --- | --- |
| Preferred | 7 | 5 |
| Substance pass | 11 | 12 |
| Substance partial | 6 | 5 |
| Substance fail | 3 | 3 |

Six ties and two “neither.” Highest-signal eight items: A5, B2, tie1.
This is a single-user, non-blind review of a repeatedly consulted development
set, not independent test accuracy, statistical significance or broad retention.

User qualitative summary: A keeps the “smartness feel” and better Turkish;
B learns exact/noun-only answers better and passes some cases A fails.
This complements the scores; it does not establish either as globally superior.

### Concrete wins and unresolved failures

- me-029/me-030: B gives the requested entity instead of restating a sentence.
- me-070: B correctly says third-attempt success does not explain earlier
  failures. A adds the unsupported need for another attempt.
- me-079: B identifies veri paylaşım rules; A focuses on their unspecified
  contents. B still adds an unnecessary caveat.
- me-050: user strongly preferred A's explanation. Agent caveat: A still does
  not fully reproduce the desired diagnosis and layout-before-purchase reasoning.
- me-090: A respects the request to vent without advice; B adds a dismissive phrase.
- me-099: A preserves “bekleniyor”; B turns an expectation into certainty.
- me-009/me-010: both fail grammar correction.
- me-049: both invent user-specific neurological explanations for morning
  lateness. User prefers A relatively but marks both fail.
- me-069: both partial, with awkward Turkish.
- Separate agent concerns, NOT changes to user grades: me-039 sharpens
  “action will be taken” into “fees will change”; me-060 categorically rejects
  leaving a key with a neighbor despite unspecified trust context.

### Disputed gold: me-089

The UI fields were checked against frozen artifacts: desired and A were NOT
swapped. The desired answer “Yeni evin henüz sana aitmiş gibi gelmiyor.” came
from an earlier assistant QA rewrite, not the user's original edited target.
Original target gave a qualified acknowledgment and practical settling-in advice.

Provenance: [QA changes](exp-009-minimal-edit/reviewed-v2/changes.json),
commit75f64e8. The user had authorized direct QA, but the assistant overinterpreted
neutral acknowledgment as requiring bare restatement. This is a reference-quality
mistake worth reporting, not hiding. It affected validation only, not A/B training.

Frozen references, generated answers and submitted grades remain unchanged.
Any correction requires a separate, explicitly documented reference version.
Sensitivity excluding this disputed item: A6/B5/tie6/neither2 over19;
A pass10/partial6/fail3, B pass12/partial4/fail3.
Do not selectively remove it solely to improve reported results.

## Operational lessons, including failed attempts

- Base-draft vLLM setup hit Qwen3.5/Transformers version incompatibilities and
  an EOS-checker misclassification. Working stack and failed logs are preserved
  in [exp009 notes](exp-009-minimal-edit/GPU-RUN-NOTES.md).
- Raising token limits does not cure repetition: exp009 greedy base generation
  looped; user-approved penalty1.05 completed all100 drafts with native stops.
- Exp010 training succeeded, but inference escalated looping budgets.
  Bounded recovery retained failures instead of relabeling them successes.
  One later EOS answer does not prove repetition is eliminated.
- Paired pod SSH initially accepted the public key but could not sign in
  BatchMode: Windows key generation had unintentionally set a quote-character
  passphrase. An existing user key unblocked setup; interactive passphrase
  removal repaired the instance-only key, verified on direct and proxy endpoints.
- Repeat smoke/tiny-overfit/pre-SFT reload were explicitly waived for A/B.
  They are recorded false/waived, not passed. Actual batch masks, imports,
  BF16/CUDA and W&B authentication were genuinely checked. Post-SFT adapter
  reload is evidenced by completed inference. Future experiments need their
  own authorized gate policy; do not silently inherit this waiver.
- A/B used the exact exp010102-package freeze. No vLLM installation for adapter
  inference. CUDA causal-conv wheel download/verification and setup logs retained.
- Supporting thinking-on/off probes were separate: base me-079 hit length limit
  without a final answer; A hit a time guard; B finished both tested prompts.
  Two prompts do not prove reasoning preservation or diagnose global collapse.

Details and fixes: [paired GPU notes](exp-012-coverage-ablation/GPU-RUN-NOTES.md),
[environment gotchas](../../../docs/environment-setup-gotchas.md).

## Recovery evidence before paid-pod shutdown

Local artifact root:
`C:\Users\cbark\Documents\llm-bender-artifacts\exp-011-012-paired`.

Archive `exp011-exp012-backup.tar.gz`:862,934,687 bytes;
SHA256 `4706aa58413f60c9f778ebdff34aab459f3192c5de630085a3e9b2b3588cbc1a`.
Archive digest and all141 indexed file sizes/hashes verified locally.
Both adapters, checkpoint30/40 optimizer/scheduler/RNG resume states, source,
configs, logs, masks, generated outputs, package/hardware inventory, W&B
history and diagnostics recovered. Code recovery bundle also saved locally.
Pinned public base weights are a download dependency, not an offline backup.
No private keys or W&B secrets belong in the journal or tracked evidence.
Do not claim measured total rental cost without provider billing records.

## Next pair: proposal, NOT executed

Working baseline A; test a narrower data intervention rather than assume that
A and B abilities can simply be combined.

- C / proposed exp013:68 unchanged A training rows +12 reviewed replacements,
  four epochs/40steps. Proposed12:4 precise extraction,4 bounded causal/evidence
  reasoning,2 Turkish grammar/precision,2 uncertainty/condition preservation.
- D / proposed exp014: EXACT same80 rows/targets as C, six epochs/60steps.
- Both independently initialized from pinned base, same LR/rank/batch/template/
  decoding. Compare C against saved A for data intervention; D against C for
  the longer schedule. No rank/LR/batch sweep in the same intervention.
- Author and review12 once; audit scenario/near-duplicate overlap before freeze.
  Never seed training from validation questions or their paraphrases.
- Preserve the20 development items; resolve me-089 reference transparently.
  Record wins, regressions and guard events, not just aggregate preference.

At proposal time no replacement12, GPU run or results existed; preparation
progress is appended below. More epochs could worsen generalization; C is not guaranteed
to inherit both A's naturalness and B's precision.

## What every future round must preserve

### 2026-10-03: C/D approved corrections and immutable freeze

User authorized the two proposed corrections and requested completion before
providing GPU access. Exported all12 actual submitted responses (7accept/5rewrite)
and preserved raw Argilla fields/answers; no live mutations or fabricated review.
Hash-bound approval records the exact user message and original snapshot/row digest.
Only tc-010 prompt hint removed and tc-005 categorical diagnosis softened to
old-cable-or-connection suspicion. All other reviewed text preserved. Two
before/after diffs link actual response IDs;68 A rows/20 validation unchanged.

One frozen shared80-row train SHA256:
`d61bdfab544dc0d3ba5531e74005940d47b6b6af38fba864dbd5ceefcf948d7a`.
Reviewed tokens5653/epoch (+5.00% vs A; draft had +3.60%). Re-audit found no
exact/near flags; all100 rows tokenized without truncation, native EOS supervised,
context masked. C/D representations match byte-for-byte,68 retained/A rows and
20 validation representations match original sources. Twelve CPU tests pass;
verify_ready.py checks file hashes, raw-review-to-QA transformations and recipes.
Every new approved rendered input/label sample saved. No model-quality result yet.

Separate reviewed C/D configs now active, four/40 versus six/60 epochs/steps;
other training/inference settings unchanged. GPU access/checks/W&B still pending.
No C/D smoke/overfit waiver inferred. GPU-HANDOFF.md warns against running the
old hardcoded A/B launcher, identifies required artifacts and future recovery.

### 2026-10-03: submitted C/D review and prompt-cue QA

All12 active-v2 candidate responses are submitted:7 accept,5 rewrite
(tc-005/006/007/008/012). Read-only API inspection; no live fields, answers or
reviews changed and no approved training artifact frozen during this check.
User asks whether explicit “do not confuse doktora” and answer-only wording
over-guide learning. Engineering judgment: answer-only wording specifies the
intended conditional output format, whereas naming the exact lexical trap is
an avoidable hint. It does not supply the person answer or constitute split
leakage, but success with that hint would not establish unprompted precision.
Recommend dropping only that hint, keeping the explicit doctoral-program context.

Additional QA on rewritten tc-005: swapping to a known-good cable and seeing
an image supports a cable/connection explanation, but “sorun kablodadır” is
over-certain if reconnection or other settings changed. Recommend conditional
evidence wording rather than an unconditional diagnosis. Proposed corrections
have not been applied; preserve actual user submissions and require explicit
authority/provenance for any post-review prompt or target change. Review
completion alone does not waive substantive QA.

### 2026-10-03: C/D preparation (no GPU, no model results)

User said “proceed.” Created exp013/014,12 drafts, shared review queue,
blocked configs, exporter that requires actual12 accept/rewrite responses,
and pre-run evaluation protocol. Preserve68 A rows in place, including every
original higher-level training row above me-040. Proposed new settings cover
ceramics/theater/battery/botany, projector/permission/podcast/version control,
polite-address/doctor-doctoral distinction, art loan and tentative festival.

CPU audit found no exact/near flags against original80/20,348 historical
benchmark entries,3500 historical training inventory entries and B's24 new rows.
These inventories overlap; do not call them unique independent questions.
All68 retained tokenizations and all20 validation tokenizations match A.
Draft target tokens5578/epoch vs A5384 (+3.60%), max train sequence514,
zero truncation, native EOS supervision and context masking verified.
Every new candidate's rendered/masked tokens saved for inspection.

Preparation caught a namesake Python-module import collision caused by older
helpers inserting sys.path entries. Restoring this experiment first fixed it;
regression test added. All ten CPU tests passed.
Live export correctly refused unreviewed tc-001; no approved data/config was
created. Old frozen experiments and Argilla annotations were not rewritten.
First queue ID4eeae7d7-af07-47d2-9673-9e368c0aed50 is superseded/preserved.
Final QA clarified tc-010: bare “doktora başvurmuş” could mean consultation
with a doctor, so v2 explicitly says “doktora programına başvurmuş.” No target
or other11 prompt changed. New active queue IDc0dc183f-e552-4a7d-9267-08211b88df94,
12 records read back and verified. Human review and GPU access are still
required. No new success claim; old queues/annotations untouched.

Details: [C preparation](exp-013-targeted-coverage-sft/README.md),
[pre-run protocol](exp-013-targeted-coverage-sft/EVALUATION.md),
[D plan](exp-014-targeted-duration-sft/README.md).

Before execution: date, hypothesis, exact changed/held-fixed variables, approved
data and split hashes, leakage checks, source/model/tokenizer revisions,
rendered examples/masks, actual settings and gate passes/waivers.

After execution: W&B IDs, checkpoint identity, raw answers, stop reasons,
failures/retries, logs/package/hardware/config snapshots, user response exports,
counts with denominators, qualitative examples and counterexamples, separate
agent interpretation, costs when measured, verified recovery manifest, decision
and next hypothesis. Append entries; do not overwrite prior findings.

Before calling the story a demonstrated success: run an untouched, independently
reviewed final test and relevant retention checks under matched protocols.
The current20 are for development; protecting train/validation separation does
not make repeated development selection an independent final evaluation.
