# Completion update

Both planned runs and all inference completed on2026-11-17. See [results](PILOT160-RESULTS.md). The plan below records the predeclared recipe; dev grading and training-backup recovery remain pending.

# Planned160-row SFT pair

Status: runnable local preparation complete; no GPU job launched. See [pod handoff](SFT160-POD-HANDOFF.md). All80 new records are submitted; [pilot160 export](sft-pilot160-v01/README.md) is frozen. Real-model launch gates remain. Current
80-row working winner is exp-006 (2e-4), based on10/6/4 owner preferences.

## Two hyperparameters, two jobs

Test learning rate and training duration using two independent runs, saving both
after3 and5 epochs. This produces a2x2 comparison without changing both variables
between the only two observable outputs.

| Planned job | Peak learning rate | Checkpoints | Hypothesis |
|---|---:|---|---|
| exp-007-sft160-lr1e4 | 1e-4 | epoch3 / epoch5 | Lower rate may preserve meaning and naturalness better on the larger corpus. |
| exp-008-sft160-lr2e4 | 2e-4 | epoch3 / epoch5 | Pilot winner may benefit from more diverse data; earlier stopping may reduce distortion. |

160 rows and effective batch8 give20 updates/epoch: save at steps60 and100.
Both jobs use the same100-step cosine horizon and6 warmup steps (same6% warmup
fraction as pilot80's3/50). Epoch3 is an early-stop checkpoint of the five-epoch
schedule, not an independently trained three-epoch cosine run that has decayed to
zero. Duration findings apply to that fixed schedule. Same seed/data order in
both runs; neither resumes an old SFT adapter or the other new run.

Keep BF16, LoRA rank32/alpha64/dropout0, the same nine target projections,
AdamW fused, weight decay0, microbatch2/accumulation4, seed3407, max length4096,
no packing, clipping1 and assistant/EOT-only supervision. Keep owner-approved
optional reasoning in the audited native template; do not invent reasoning for
simple questions. Audit actual nonempty reasoning and native empty blocks again.

Training initialization remains fresh LoRA on the pinned CPT-merged parent:
LiquidAI revision `0dc4268b561499c648c7ba7c9466bf3d8d01517a` plus CPT revision
`6f213ec25a944dab2fbdeb6d337deb0e0442e638`. Untouched LiquidAI at the same parent
revision is the PRIMARY EVALUATION BASELINE per owner request. Changing the
comparator does not change initialization; this pair does not isolate CPT's value.

## Dataset and launch gates

[Batch02 text editor](http://127.0.0.1:6900/dataset/2622bd70-e5e5-48af-8905-91a4ea47032f/annotation-mode)
has20 NEW rows each from public Occam, Turkish-SFT, Atlas and CoT. Occam20 retain
standing owner approval. Owner now edits Input, optional Thinking and Output only,
without quality selections. All80 final responses have now been submitted and exported, preserving earlier
owner edits and Occam approval. The combined160 contains30 nonempty reasoning examples. Blank Thinking must not fall back to source reasoning.
Replace unusable examples before claiming160 accepted training examples.

Merge accepted new80 with the semantically corrected old80. Preserve originals,
edits and pinned source IDs. Recheck deduplication, leakage, task coverage, native
labels, EOS and rendered lengths after edits. Never import test/benchmark items or
their corrected/paraphrased variants. Raw batch count balance is not token balance:
Turkish-SFT contributes36,190/61,103 target tokens (59.2%), CoT21,095 (34.5%).
Final160 target token shares are Occam5.9%, Turkish-SFT43.1%, Atlas16.6%, CoT34.3%; see the frozen manifest. Do not silently truncate or duplicate short rows.

A separate authored20-row development set and selection rubric are now frozen in
`sft160-dev-v01/`, covering natural Turkish,
faithful edits, grounded answers/clarification, exact constraints and verified
reasoning. Separate source/document/template families where feasible. Existing20
stay diagnostic evaluation-only; reserve a fresh final test before release claims.
Re-run real-model smoke/tiny-overfit checks; old80-row gates do not validate edits.

The existing run_lfm3_sft_pilot.py hardcodes80 rows and old paths: it must NOT be
launched unchanged for160. Versioned `run_lfm3_sft160.py` and `run_lfm3_sft160_pair.py` now support160,
isolated exp007/008 artifacts and intermediate saves. Save adapters/tokenizers,
optimizer/scheduler/RNG states, training logs and provenance for both checkpoints.
The old pilot did not retain optimizer-resume state.

## Evaluation

Evaluate all four checkpoints on the same new development packet, using paired
preferences/notes when useful and objective checks for numeric answers, meaning
preservation, constraints, repetition and grounding. Freeze the dev metric/rubric
and regression budgets before launch. Select by development evidence, never loss;
prefer an earlier checkpoint when quality is practically tied.

Compare the selected candidate to untouched LiquidAI under identical prompts,
template controls, decoding and token budgets. Retain CETVEL100 as development-only
and TurBLiMP1600 as supporting regression evidence. Reuse vLLM BF16, context8192,
max new4096, temperature0.1, top-k50, top-p1, repetition penalty1.1, seed3407,
explicit stop124900 and the same loop guard. Verify native base/SFT stop behavior.
Generate the actual untouched baseline before claiming base-to-SFT gains.

Keep thinking disabled in the primary comparison to match the prior protocol.
Freeze a separate thinking-on/off development comparison on verified reasoning
questions at matched budgets before claiming a benefit; inspect rationale and
final answer. That is an inference comparison, not another training recipe.
No training or pod provisioning is launched by this plan.

Local preflight (2026-11-17): native rendering, explicit masking and EOT labels passed for160 rows;30 nonempty reasoning traces, longest2289 tokens, zero truncation/zero-target rows. See `sft-pilot160-v01/preflight-local.json`. Real-model gates remain mandatory on the new GPU.
