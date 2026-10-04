# Experiment journal and blog evidence trail

Updated: 2026-10-04. Owner request: preserve what we tried, results, failures,
fixes and decisions so a later blog can tell the complete story.
This is an evidence journal, not a claim that the project has already succeeded.
Append dated entries for every future round; preserve previous snapshots.

### 2026-10-04: E/F GPU pipeline launch (not a quality result)

Later on this same turn user explicitly requested skipping smoke/tiny and directly
training/inferencing this pair. E checks were already finished and full SFT was
running. Paused only orchestrationPID816, not its trainer, to prevent future F
diagnostics; E completed uninterrupted40steps/4epochs in110seconds, train loss
1.223. W&B64a31c42, exp015-sft-target-quality-80rows-40steps. No quality claim.
Resume path preserves completed base/C/E stages and full E state; F does only
actual masks plus W&B, reuses same-pod E reload proof for identical LoRA stack,
records smoke/tiny as explicitly waived NOT passed, trains fresh base40steps and
reloads final F for inference. Trainer waiver policy restricted to E/F smoke/tiny;
no data/LR/rank/step or evaluation-code changes. Source revisions/logs kept.
Default SCP download stalled/reset; classic SCP(-O) recovered source bundle with
matching SHA c42e756814d5c2c43013ec010a66844f5818a6117d29bd1a8965d9f2bfbb4161.
One later SSH banner timed out; retry worked. Root cause not established.

User supplied direct81.27.69.180:52991/proxyssh7.vast.ai:36350 and existing public
key. Direct authenticated successfully; recorded new host key on first contact,
no mismatch verification bypass. RTX4090/24564MiB, driver565.77, CUDA maximum
reported12.7. Exact prior102-package Python3.11.16/Torch2.7.1+cu128/Unsloth2026.9.6
freeze reused; official causal-conv wheel SHA verified. Actual CUDA/BF16/import
and base generation work on this driver; no CUDA13/vLLM/unconstrained installs.
Standalone setup requirements path satisfied at /exp-010-lr-ablation; CRLF
normalized before Linux execution. Setup log and script will be recovered.

Frozen source347b563487bf9a9ffcb5361ad964b23d2e68e191 cloned clean from Git bundle;
no .env/private key transferred. C adapter from verified prior recovery matches
SHA9578cf7bc6537927bd4ec483b67c5c8f06cf627b86d07c5b278523809db36d36.
W&B authenticated as c-barkinozer using credential streamed from local.env into
launcher stdin/process memory. Detached pipelinePID816 began canonical base32
inference. Old waiver is not inherited; genuine per-arm checks remain required.
Fresh E/F40steps each and final40 inference are scheduled, not claimed complete.

New execution code honors80/104 rows/40steps, asserts final step and records
actual training microbatch token exposure. CPU preparation12tests plus3execution
tests passed. Importer and recovery tools committed separately84cfc34/44d8c41;
they do not change the running training/evaluation source revision. Blind
balanced P/Q/R/S mapping stays external and is not exposed through UI fields.
Outputs will have independent semantic/Turkish/style grading, not automatic
quality claims from loss/length/Markdown flags. All artifact recovery and human
evaluation remain outstanding at this entry.

### 2026-10-04: E/F reviews exported, final split leakage audit

User completed all33 training/12 control records and requested leak confirmation.
Read-only export preserves raw Argilla submissions, fields, IDs, timestamps and
user-reviewed answers: train31rewrite/2accept, controls12rewrite. No field/review
mutation or agent target rewrite. Frozen E80/F104,9 actual target changes versus
C,71 E rows unchanged, all80 question IDs/messages/order/categories preserved.
F first80 rows/tokenization exactly E. Original20 validation SHA unchanged.

Final training artifact hashes E
`2dc3724451a1e8a2bd33a585e71a8c0d533d68b92da3355363497c905b43d1ea`, F
`fe8ff4c9ff74a8618754bd2f5c25d1794bad9263cbc5fa3a436d593599085950`.
Controls SHA `21f46cef4d1e80dbde9ea5db69ea83b409efc67ae6c17260a411938b35dabd05`.
Final supervised tokens per dataset E5121/F6216; maximum sequence514, no truncation.
Both pinned tokenizer preflights passed nativeEOS/context masking and old20 parity.
No model inference, GPU training or W&B run was started.

Expanded final audit E80×32=2560/F104×32=3328 (5888 overlapping comparisons):
zero exact prompt/near0.60/5word-containment0.50/long exact answer/embedded eval
text flags, zero scenario/ID/composite-source overlaps. Earlier inventory scan
repeated on approved data. Inspected nearest-pair listings for all32 and semantic
boundaries. Only shared exact target: new021/control012 "Tamam, dinliyorum.";
conventional2-word listening response retained, not heldout factual leakage.
Some task families intentionally shared; not a novel-task benchmark. Same-author
synthetic controls/only12/reused20 limit independence and generalization claims.
Outcome: no identified item-level leakage, NOT universal semantic/pretraining
guarantee. Controls physically separate from train/validation loss, runtime
loaded-ID/mask checks still required. CPU readiness plus12 preparation tests pass.
Evidence: [final reviewed leakage signoff](exp-015-target-quality-sft/data-reviewed-v1/SEMANTIC-LEAKAGE-REVIEW.md).

### 2026-10-04: approved E/F hypotheses, data preparation only

User accepted exp015/016. E tests necessary target-answer repair on exact C80
questions; F adds24 independent examples (4×6skills) at fixed40optimizer steps.
All LR/rank/batch/base/masks held; fresh base independently, not adapter stacking.
Common40-step cosine horizon/warmup2; E4passes, F roughly3.08passes. Addition
changes composition/row exposures and tokens, not a pure diversity causal test.
Audit24 existing records:9 repairs,15 correct targets retained,56 others intact.
No forced summary rewrite: those targets already preserve source meaning.
Draft E5133 vs C5653 target tokens (-9.2%); F6179 (+20.4% vs E) per full dataset.
Per-dataset totals are not runtime40-step token exposure. No forgetting claims.

Separate12 controls (2×6skills), never optimizer/replay/validation loss. Original
20 remain unchanged incl disputed089. Plan same-backend base/C/E/F generation,
balanced blinded positions, explicit best-set ties and semantic/Turkish/style
grades separately. Prior A/C/D Cem Öztürk summary all invented a price-change
commitment; no general unsupported-inference avoidance claim for C.

Preparation v1 omitted historical CSV train inventories; fixed in v2 and regression
tested. A manual semantic check found v2 control010 too similar to old B's
resolved-file-format case. Replaced with independent atlas-purpose case in v3;
old snapshots/control queue retained, new control queue versioned, no reviews
modified. Active v3 checks348 historical benchmark entries +3500 historical
training entries +24 B entries (overlapping inventories, not unique questions),
current80/20, new24 and controls12. No detected exact/near flags; not proof of
universal semantic independence. Final12 pair-preparation tests and4 existing
tokenizer/masking regression tests passed. Both active UI routes returnedHTTP200
and API readback verified all33/12 fields and IDs. No approved data exists yet.

Shared GPU runner had80rows/epoch-only settings hard-coded. Added explicit
configured counts/max_steps/step saving/eval while retaining old config defaults;
draft-human-review block remains. CPU tested, GPU untested. No weights/inference,
W&B or GPU rental/termination here. Data review queues:33train and12controls.
User work next: accept/rewrite/reject; no trainable approved artifact yet.

Full plan and evidence: [exp015](exp-015-target-quality-sft/README.md),
[exp016](exp-016-diverse-coverage-sft/README.md).

### 2026-10-04: completed original A/C/D human review

User rejected switching to the new tie-specific v2 queue and completed all20
original records. Read-only export: snapshot SHA256
`c9da2d9b06bad63e6bd6c51c9beefc38a8456595b7065b43cd331a548df812be`.
UTC export timestamp21:15 on Oct03 corresponds to Oct04 local Istanbul time.
Structured substance counts A9pass/6partial/5fail,C11/5/4,D10/5/5.
Each arm sole preferred3; tie9,neither2. Notes resolve020 A=D>C and029 C=D;
seven ties unspecified.060 C selection vs A=C>D note, and069 A partial label
vs pass prose preserved without overriding. No need to redo user's review.

Eight predeclared high-signal items: A2/5/1,C3/3/2,D2/4/2. Excluding disputed
089 leaves all19 A9/5/5,C11/5/3,D10/4/5, with the same general conclusion.
C/A adds pass029/069/079 but loses059;029 is answer-format gain, not new fact.
D/C gains059/070 but loses069/079/090;049 improves only to partial,050 becomes
fail with619tokens/repetition/contradictions. All fail grammar009/010.
C1030 vs D1569 tokens, medians22/37, all nativeEOS; technical stop success
does not hide semantic repetition. Lower D train loss did not reliably help.

Agent recommendation: retain A as established comparison, C as candidate;
do not promote D or declare an overall winner. Prioritize independent coverage
for mechanisms/trade-offs/grammar/interaction, not blindly more epochs. No
new experiments or training targets created from validation scenarios here.
This is single-reviewer/seed, non-blind reused development, not final accuracy.
Full evidence and per-item notes:
[C/D human review](exp-013-targeted-coverage-sft/human-validation-review-v1/README.md).

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

### 2026-10-03: C/D execution, observations and verified pod recovery

User supplied proxy19764/direct43254 and explicitly waived smoke/tiny-overfit,
requested uninterrupted two-run SFT,inference,comparison and complete backup.
Separate scoped C/D gate policy recordedfalse/waived for smoke,tiny and pre-SFT
diagnostic reload; actual100-row masks and W&B authentication genuinely passed.
Fresh base independently; same80 reviewed targets,4/40 vs6/60 epochs/steps.
Training sourcef47abd7; exact102-package freeze matches A/B. Setup used prior
hash-verified196MB CUDA wheel instead of redownloading; same pinned packages.

C:153.696seconds,mean loss1.1909237187355757,W&Bf71c7df3,
nameexp013-sft-targeted-80rows-4ep. D:132.0165seconds,mean
loss0.9682095202306906,W&B9e6ad1e3,nameexp014-sft-targeted-80rows-6ep.
Both finished. Initial compilation makes runtime comparison non-isolated.
Both20 primary outputs native EOS; no guards/length/time stops. Same inputs,
render/template/decoding/reference parity with saved A confirmed. C tokens
total1030/median22/max188; D1569/37/619. Scheduled final adapters preselected;
C30/40 and D50/60 retained full resume states,not all epoch checkpoints.

Preliminary agent inspection,NOT user grades: C029 exact entity and C079
veri/vergi extraction improve selected A weaknesses; both099 preserve
expectation.009/010 grammar failures and049 unsupported neurological causation
persist. C070 still adds illogical reasoning. D050 expands into619tokens with
contradictions/repeated list advice; D089 dubious alone-at-home claims and D090
generic reassurance remain concerning. Lower D loss does NOT establish a gain;
additional epochs are not currently a demonstrated cure. No global forgetting,
reasoning-collapse or no-hallucination conclusion from20 development questions.
Regex bold/headings/emoji flags0/20 each,not evidence of semantic quality.

Argilla desired/A/C/D20,datasete3b691cb-79fc-4bd8-a358-39f9a23770b5,
fields strictly source-bound and read-back verified,HTTP200. Old reviews untouched;
me-089 reference dispute displayed. Human comparison pending,not promoted.

Recovered local root:C:/Users/cbark/Documents/llm-bender-artifacts/exp-013-014-paired.
Archive847,921,015bytes,SHA256
7ec4c82c39f02a12583d5a885e60736252160872c4b395e4c964916b4bcfe864.
Full digest plus all129 file sizes/hashes verified; bounded extraction and
adapter/inference/resume-state parity checked. Source/config/log/package/platform,
W&B history/local files,raw outputs and post-SFT reload evidence saved. Credential
used is absent from recovered files. Public pinned base weights still require
download; no offline/bitwise reproduction claim. GPU can be terminated; agent
did not shut it down. Actual provider billed cost not measured.

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
