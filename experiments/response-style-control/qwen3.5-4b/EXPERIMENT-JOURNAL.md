# Experiment journal and blog evidence trail

Updated: 2026-10-04. Owner request: preserve what we tried, results, failures,
fixes and decisions so a later blog can tell the complete story.
This is an evidence journal, not a claim that the project has already succeeded.
Append dated entries for every future round; preserve previous snapshots.

### 2026-10-04: human30 complete; selected F and closed this SFT phase

Actual30 Argilla submissions exported read-only. F19 preferences/base6/tie2/
neither3; grades F23pass/4partial/3fail versus base21/3/6. QA12/12 pass BOTH,
all12 prefer F. GEC4/6 vs0/6 pass; translation5/6 each with balanced preferences.
Summary pass F2/6 vs base4/6, preferences base4/F1/neither1 despite higher ROUGE.
One reviewer; latest30 notes blank. User-supplied other-AI critique is qualitative
feedback, not a second saved blind rating. Do not infer zero capability damage.

User chose to close the phase and share adapter/dataset/model card and Turkish
journey blog. F step40 selected as a usable experimental Turkish response-style
candidate, not a certified general Turkish upgrade. No new GPU task or training.
Source configs/results remain immutable; phase-closure.json records lifecycle.
HF cards/blog/guide and local hash-checking builder prepared in docs/publication.
Public upload and GitHub push not performed; owner IDs, licenses and historical
synthetic/personal-assistant terms/provenance need completion before redistribution.
External CETVEL source-bearing files stay local, not auto-relicensed as SFT data.
All recovery archives/weights remain outside Git; no secrets or keys in new cards.
Deferred future work: faithful summary, de/da, correct-input preservation, fresh
retention tests; agentic RL remains a separate planned track.

### 2026-10-04: human20 completed; freeze fresh500 before changing F

Fresh500 subsequently completed1000 outputs, scoring and paired bootstrap in
1215.82seconds (~20m16s), excluding setup/download/recovery.45 files and both
500-output hashes/config/prompt/token/package parity verified locally before
declaring GPU safe to close. Archive SHAabcd9cc94a7562e8c7f6a70685aa11ba54e39d0f81b4666a2f610035dc7ecf5a.
GEC EM0/100 to30/100; TQUAD F1.2006 to.6458 (EM0 to36), XQuAD F1.1368 to.5584
(EM0 to29). Translation BLEU16.84 to16.81/chrF52.16 to52.43, mean-sentence-chrF
paired95% interval includes zero. Summary ROUGE-L.1845 to.2093, paired difference
interval.0118 to.0380. Strong reference/compliance signal, not proven semantic
knowledge or general Turkish improvement. Pilot QA human grades already showed
both arms correct despite automatic score gaps; keep this warning in blog claims.
Base496 nativeEOS plus4 repetition guards; F499 plus1 repetition guard at
tquad-00747. All retained/scored, no retries or silent filtering. No length/wall
terminations; final long F answer eventually reached EOS. Median tokens98/26.
Blind30 queue1ddfe4d9-5d36-46bc-a1c8-0ebc4959c941 created,6/task frozen before
outputs, P/Q shuffled; all30 fields and HTTP200 verified. Private map external.
Review pending, no agent-authored judgments or new fine-tune/W&B. GPU work complete.

New GPU then supplied: direct143.131.225.132:41841 and proxyssh9.vast.ai:19562
accepted established key, same containerc9995edb168b. No key content in Markdown.
RTX4090/24GB, driver590.48.01,80GB workspace,Python3.12.3; pinned vLLM0.30.0,
Torch2.13.0+cu130,Transformers5.18.0 CUDA/import checks passed. Source archive
SHAe26142ffc6c6600d874f16ae550089a7871b7effd444775d7619278ea252e789.
Adapter extraction tried before asynchronous SCP completion: unexpected EOF,
not a model/benchmark failure. Waited for transfer exit0, archive SHA matched,
re-extracted and weight/config hashes passed before generation. Reusable note added.
Detached launch_remote.py queued setup-waiting coordinator; no W&B/training,
no extra smoke/overfit. At this update pinned base download ongoing, no scores yet.

Exported actual Argilla20/20 submissions read-only, verified raw answers and
external blind mapping. One missing submission arrived during export; no agent
labels authored. F preference12/base2/tie4/neither2, passes F13/base12;
partials F5/base6, fails2 each. QA all8 pass for both arms, indicating much of
automatic QA gain is compliance rather than proven knowledge improvement.
GEC reviewed4: zero pass for either. Translation base3pass/F2; summaries base1/F3.
Notes flag de/da, question particle/person, over-correction, translation roles,
summary attribution/negation. Preserve even notes/grade inconsistencies; no
silent regrading. Strong useful preference signal, limited correctness evidence.

User decision: no de/da fix yet. Freeze final F; characterize weaknesses with
500 NEW balanced generation questions, then decide training. Created
turkish-capability/qwen3.5-4b/exp-003-cetvel-500. Full pinned source splits,
not old700 leftovers. Excluded historical700 rows/source groups and pilot100;
one question per source group, seeded selection, training104 string screening,
conservative near-source withholding. All700 historical documents/prompts/targets
verified against downloaded sources before selection. TQUAD string ID/int offsets
match HF schema; official MLSum converted-Parquet separately pinned/hashed.
One near-source summary candidate withheld, no selected training candidate;
maximum input3410, no truncation or budget-driven omission encountered.
500 SHA2ccd068e8f95259083f0f5c30853d414801b9e06e9790bcf936b471467c46b93.
Human30 chosen before model outputs. Same vLLM generation settings/F hashes.
Prepared1000-output coordinator, task scores, paired bootstrap and recovery.
Six new CPU tests and four pilot tests pass; GPU execution NOT performed.
Both previous SSH routes unavailable (direct timeout/proxy refusal); need new GPU.
No new fine-tune/W&B. If future training uses500 feedback,500 becomes development
and needs a fresh final test; never train these rows/targets/paraphrases.

### 2026-10-04: CETVEL-tiny200 inference completed and recovered

Base100/F100 same-engine outputs and task-native scores completed;290.56seconds
for benchmark plus scoring, excluding setup. Verified62 recovered file hashes,
200 outputs, prompt/config/package parity and final F adapter identity before
announcing GPU safe to close. No W&B or new training. Local evidence and report:
turkish-capability/qwen3.5-4b/exp-002-cetvel-tiny/results-v1 and REPORT.md.

GEC exact base0/20,F6/20; TQUAD EM0/20 versus8/20,F1.2044 versus.7219;
XQuAD EM0/20 versus11/20,F1.1292 versus.6083. Translation BLEU12.63 versus12.39,
chrF52.82 versus53.84: mixed. Summary ROUGE-L.1791 versus.2289. Base96 nativeEOS
and4 repetition guards; F100 nativeEOS. Guarded answers retained, no retry.
Median output83 versus24.5tokens. Strong compliance/reference-overlap signal,
not established general fluency/semantic superiority; extra prose affects scores.

Created frozen blind20 Argilla queue f6719ded-3baf-4d32-bbf2-885e175f1413:
4/task preselected before outputs, balanced shuffled P/Q, both grades and best
P/Q/tie/neither. Verified20 raw-output fields and HTTP200. Private mapping outside
Git, no human judgments authored by agent. Human review pending, then decide
whether to confirm on fresh additional300/500 source groups. No benchmark training.

### 2026-10-04: CETVEL-tiny GPU authentication and fast engine preparation

Non-benchmark probes also caught two API compatibility issues before the100-row
benchmark: Transformers5.18 tokenized chat rendering returned a dict-like object
without explicitreturn_dict=False; vLLM0.30 add_request returned randomized
internal IDs but outputs used external IDs. Fixed explicit token-list contract
and external-ID routing with fail-loud empty-engine check. Stopped only the owned
diagnostic parent/core for the routing issue; no benchmark restarted or altered.
All4 corrected probe base/F outputs reached modelEOS248044. Actual benchmark then
launched; no training/smoke/overfit or W&B. Detailed reusable fixes in gotchas.

Established default key rejected at both direct83.195.246.217:50675 and
proxyssh2.vast.ai:14266. Private/public pair matched; server rejected the offer.
New per-instance Ed25519 key, blank passphrase viaPTY, attached by user, then
BatchMode/IdentitiesOnly authenticated both routes to containerd8a5dd33868f.
No key content in Markdown or repository. Server-side cause not established.
Reusable procedure added to environment-setup-gotchas.md.

RTX4090,driver595.71.05,CUDA maximum13.2,Python3.12.3. vLLM0.30.0 and
Torch2.13.0+cu130 installed in persistent venv; import/CUDA passed. Base download
completed~72seconds; final F weight/config hashes verified before transfer.
User explicitly permits vLLM if worthwhile. Same-engine base/F batch8,context8192,
eager/no-prefix-cache,BF16,output4096 is explicit fast-protocol amendment;
preselected human20 unchanged. No inference/training/W&B result claimed yet.
Initial probe stopped at a tokenizer-EOS assertion before generation: tokenizer
im_end248046 versus modelendoftext248044. Corrected by reading model config and
explicitly matching earlier HF248044 stop, not treating im_end as native modelEOS.
Logs retained. Benchmark remains pending until LoRA/EOS execution is verified.

HF upstream metadata confirms both pinned Qwen/Unsloth safetensors shards have
identical content hashes; prior wording implying different weights was corrected.
Config/template/tokenizer files differ. Base rerun justified by stop/cap/backend
changes, not repository branding. No benchmark rows used for compatibility probe.

### 2026-10-04: freeze external CETVEL-tiny100 base/F pilot

User requested an external100-question pilot before larger300/500 evaluation.
Located historical CETVEL-mini700, not500:200GEC,150TQUAD,150XQuAD,100translation,
100summaries, originally task-prefix pools. New exp002 under turkish-capability
is evaluation only. Seeded20-per-task subset selected from frozen input/document
fields without consulting old outputs/scores.100 question SHA
6bfb23966fb8e8bea277fc8a6f912ac404fc3d1a4d24c2dd669670ef35057310.
Existing documents/references/prompts preserved. Not all-CETVEL representative,
no MCQ included, not a pristine unseen holdout because old diagnostic was inspected.
F104 exact/near-string screening zero candidates; no semantic-independence proof.
Tokenizer profile100inputs maximum1487, no input truncation; four CPU tests pass.

Planned same pinned unsloth base/exp016 final40 F, BF16 HF/Unsloth batch1,
thinkingoff/greedy/rep1.05/output4096/context32768,180s/exact-loop guards, nativeEOS.
Removing CETVEL's small caps/newline stops is explicit protocol adaptation, not
official CETVEL scores. Existing task-native scorers reused; human20 selected
before outputs. No training, no W&B, no model judge calls. Local final F identity
preserved by recorded weight/config SHA. Scripts prepared; GPU inference NOT run.
Need new GPU address. Future benchmark-guided tuning makes tiny100 development;
confirmation must use additional fresh rows/source groups, never train targets.

### 2026-10-04: simplify E/F human review at user request

Review subsequently completed32/32 and exported read-only to exp015/human-review-v3.
Full32 pass/partial/fail: base17/11/4, C23/3/6, E24/3/5, F26/3/3.
EvsC gains two pass records but loses one; FvsE gains two without pass losses.
F is the strongest observed grade candidate, not proven general superiority.
Old20 F14/3/3 versus E12/3/5; both E/F new12 all pass. Fourteen ties remain
unallocated; preferences base2/C4/E4/F6, neither2. Preserve exact review notes,
timestamps and external raw API snapshot; no annotations created by agent.
User requested avoiding repeated all-pass review. Partitioned future manual
focus16/regression-watch16 with IDs and selection provenance. None deleted from
Argilla or frozen validation; no training reuse. Keep full32 inference and
denominators; inspect changed/new failing watch outputs, reuse grades only for
identical prompt/output/settings with provenance. All-pass16 outputs are not
all byte-identical, so do not label them identical ties or permanently solved.
Focus is an outcome-selected diagnostic slice, not a replacement full benchmark.

User immediately clarified the requested layout: keep best P/Q/R/S/tie/neither
plus one pass/partial/fail grade each for P/Q/R/S. Active v3 dataset
ff9f4e4c-796b-4595-aa33-0229137b6258 now has these five required questions and
optional notes. Tie guidance asks for exact tied positions in notes; absent notes
cannot be treated as a known subset. Both prior queues preserved with zero saved
responses at v3 creation; external snapshot retained. Answers and balanced mapping
unchanged/read-back verified. Report one grade per output, not separate axis rates.
The v2 creation below is retained as superseded interface history.

User found the32-item detailed queue too complicated. Created a separate v2 queue
with only one required best-output multi-selection and optional notes. Dataset
5d0f657e-0abe-49cf-865b-d2800028a273; old detailed queue unchanged, zero saved
responses at creation, read-only snapshot stored with external review artifacts.
All32 original conversations/references and128 output strings verified against
frozen artifacts and original queue. Same balanced private P/Q/R/S mapping;
no new inference or changes to answers, data or model settings. Model identities
remain hidden. me089 reference warning preserved. Importer is idempotent and checks
all fields without overwriting responses. Categories/termination retained in raw
artifacts, omitted from UI clutter. v2 is an explicit post-output usability-driven
scoring change: report preferences/qualitative notes, not invented per-axis grades
or claims of semantic accuracy improvement. Historical v1 protocol retained.

### 2026-10-04: E/F complete; urgent essential recovery verified

E80rows/40steps/4epochs,110.012seconds,train loss1.2226915773;
W&B64a31c42. F104rows/40steps/3.076923epochs,106.8984seconds,loss1.3473353401;
W&B3a59cda8. Fresh base each, unchanged approved data/LR/rank/scheduler/seed.
Different target distributions mean these losses are not a quality ranking.
320actual microbatches each: E20484supervised/38472input tokens;
F19131supervised/37334input (-6.61%target exposure versusE despite more rows).
Final40selected beforehand; no control-based checkpoint/data selection.

128/128canonical base/C/E/F answers nativeEOS; render/token parity verified.
C's old20 regenerated answers AND output token IDs exactly20/20same as saved C.
Blind32 UI created/read-back verified, including desired answers; balancedP/Q/R/S
mapping stays external, no model identity in fields. Separate semantic/Turkish/style
ratings and explicit multi-selected best outputs. Dataset3b2cf5b1-13d2-4ea1-859b-2faa16c029ad.
No semantic improvement/generalization or overall winner claimed before review.

Full1,447,180,265-byte archive SHA800cdf2dd663cc7eae1bccb43d0273cb762fbcaacb9d897637ef12d48dca8a36
passed206internal file checks on pod, but NOT fully downloaded locally.
Transfers hit SSH banner/KEX/connect/keepalive timeouts and resets on both direct
and proxy routes. ClassicSCP(-O) helped transport but did not eliminate failures;
proxy matched container55d58cf4f885. Loopback HTTP through encrypted SSH tunnel
test was also slow (~1.5MB/120seconds); local test tunnel stopped, no public HTTP
listener/upload. Root cause not established; do not label this a training failure.
64MiB parts resized4MiB;95smaller chunks salvaged from prior complete/partial files
only after matching independently recorded hashes. Later four parallel small
transfers improved throughput. Retained partial full-backup files are not a valid
whole backup and must not be confused with verified recovery.

User urgently prioritized GPU deletion in5-10minutes; explicitly narrowed scope
to essentials and deferred local paperwork. Created188,913,259-byte essential
archive SHA2ca2d0021908f1f76470f7baff690ece83fd259b579487c7426511e2eabe2a0e.
All46parts, whole archive and155included files verified locally, both final
adapters verified against inference hashes,128outputs/configs/globalstep40/W&B
finished checks passed. Sources347b563(E) and77f2361(F) both bundled; split change
is only orchestration/gate waiver and evidence tools, not different optimization.
Final adapters, tokenizers, logs/configs/masks/exposure, W&B history/summary/binary
logs, source/data revisions retained. Base weights remain pinned public dependency.
Omitted optimizer/scheduler/RNG resume binaries, intermediate checkpoint weights,
diagnostic adapter weights; wheel/C comparator already in prior verified local
recovery. Exact checkpoint resume unavailable, reproducible fresh rerun still
possible. User told GPU safe to close only after successful local verification;
agent did not stop/destroy instance.85small evidence files exported toGit;
weights/private blind mapping remain external under Documents/llm-bender-artifacts/exp-015-016-paired/essential-extracted.

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
