# Turkish without forgetting: self-distilled SFT plan (2026-11-21)

Status: plan only. Nothing trained, generated or published. Supersedes the
"scale authored rows to 6000" idea discussed on 2026-11-21.

Goal (owner): meaningful, grammatical Turkish (understanding and writing) for
LFM3-1.7B, while model-card abilities (tool calling, math, coding, instruction
following) do not drop much. World knowledge and the other 15 languages may be
sacrificed; English must stay. Budget: RTX 4090 on Vast at about $0.40/h,
$30-60 total, plus writer/fixer API cost.

## 1. What our logs already establish (do not re-test)

- **D1: Turkish input is a bottleneck, not only Turkish output.** Base solves
  English arithmetic word problems 8/8 but Turkish 4/8 (TR->TR), fresh holdout
  3/7 vs 7/7, and misreads Turkish inputs ([CROSSLINGUAL-DIAGNOSIS](CROSSLINGUAL-DIAGNOSIS.md),
  [BILINGUAL-FINAL-REVIEW](BILINGUAL-FINAL-REVIEW.md)).
- **D2: Every SFT run so far damaged thinking-off arithmetic.** Base 8/8; exp012,
  exp013, Turkish60, bilingual69 0-1/8; exp014/015 1-2/8 off, 8/8 only with
  thinking on ([PRESERVATION-SESSION-RESULTS](PRESERVATION-SESSION-RESULTS.md),
  [COOKBOOK-SESSION-RESULTS](COOKBOOK-SESSION-RESULTS.md)). Parent, LR, mask,
  framework and an 80-row verified retention mix were all varied; it persisted.
- **The one variable never varied: who wrote the targets.** All five runs train on
  externally authored, concise answers (520/640 direct rows; exp013 retention rows
  are also "concise final answers"). Base computes inline (median 145 tokens,
  thinking off); SFT models answer in ~50 tokens and stop computing. LFM3 was
  post-trained on 1.75T SFT tokens + RL with a length penalty + on-policy
  distillation (model card); ~145k off-policy target tokens are enough to move
  that policy. This matches "spurious forgetting" (task alignment lost, knowledge
  intact) and SDFT's distribution-gap explanation. It is a hypothesis, not proven.
- **D3: CPT on the post-trained checkpoint helps language modeling, hurts chat.**
  Grammar 71.8 -> 80.3, Wiki NLL 3.26 -> 2.39, but EOS stops 100 -> 56 and task
  scores fall ([CPT-FAST100-RESULTS](CPT-FAST100-RESULTS.md)). Liquid's own CPT
  notebook says: "For large CPT runs, consider starting from the base checkpoint."
- **D4: Our evaluation cannot detect moderate changes.** 8 symbolic controls,
  16-35 preference groups, owner + AI-assisted judgments, single seed, every
  bootstrap interval includes zero. Decisions are currently made on noise.

## 2. Review of "writer AI + fixer AI -> 6000 rows, spot-check samples"

Keep: more data, two-model quality control, owner spot checks.

Risks if the AIs write the answers:
1. **Scales D2.** Ten times more off-policy, teacher-style answers = ten times
   more pull away from LFM3's own distribution. Expect worse math/tool retention,
   not better (SDFT: larger distribution gap -> more forgetting).
2. **Translationese.** Translated SFT data loses to native data on generative
   tasks; round-trip from native beats single-pass from English (Chen et al. 2024).
3. **Teacher thinking is off-distribution**, and thinking in the user's language
   costs accuracy (Qi et al. 2025). Do not author Turkish reasoning traces.
4. **Concision fights reasoning at 1.7B.** Liquid already trained conciseness with
   RL; Occam-style short targets remove inline computation (D2).
5. **Spot checks catch grammar, not meaning.** Our own failures are reversed roles,
   wrong units, numbers changed: these need automatic invariant checks.
6. **Same-family writer and fixer** tend to approve each other's errors.
7. **Provider terms.** Check that both providers allow training on outputs
   (see the existing `bilingual-pilot-v01/TERMS-RESTRICTION.md`).

## 3. Recommended approach: self-distilled Turkish targets

Principle: **the model writes its own answers; the AIs only translate.** LFM3
answers the English version of each task in its native mode; only verified answers
are kept; the writer AI renders that answer into Turkish without changing content;
the fixer AI checks grammar and meaning. The model then only has to learn
(a) Turkish input -> the same internal problem, and (b) its own content in Turkish.
This is SDRRL (Zhang et al. 2024) plus SDFT (Yang et al. 2024) plus rejection
sampling, adapted to a reasoning model.

Per task group (EN prompt `p_en`, TR prompt `p_tr`):

1. Generate k=4 LFM3 samples for `p_en` with the model-card preset for the task
   (math/STEM: T=1.0, top_p 0.95, top_k 20; other: T=0.1, top_k 50, rp 1.1),
   thinking on where the base uses it.
2. Verify: math exact value, code unit tests, tool call JSON == gold (name, args),
   instruction constraints by checker, general tasks by fixer-AI equivalence to the
   reference. Keep one verified sample; drop the group if none passes (report the
   drop rate per category).
3. Writer AI renders only the final answer to natural Turkish; numbers, names,
   code, JSON, units must be byte-identical or rule-checked. Fixer AI (different
   family) grades grammar and semantic equivalence; failures are rewritten once,
   then dropped.
4. Rows (native chat template, completion-only loss, verified masks):
   - `tr->tr`: user `p_tr`; thinking = model's own English reasoning (unchanged);
     answer = Turkish rendering.
   - `en->tr`: user `p_en` + "answer in Turkish"; same target.
   - `tr->en`: user `p_tr` + "answer in English"; target = model's own answer.
   - `en->en`: model's own output unchanged (replay anchor, near-zero loss).
   Thinking-off rows keep the model's own inline computation in the answer.

Data sources for scaling (licenses to verify before use): native Turkish prompts
first (round-trip TR -> EN -> model -> TR), e.g. the Aya dataset Turkish subset;
GSM8K **train** split (never test); code with tests (MBPP train); function-calling
sets with gold calls; IFEval-style checkable constraints; general chat prompts.
Target mix for the 6k step: 35% math, 15% code, 15% tool calls, 10% constrained
instructions, 25% general chat/writing, plus about 30% English replay on top.

## 3b. Owner proposal and agreed revisions (2026-11-21, later the same day)

Owner proposal: take 10 rows from each model-card benchmark (about 300), hold out
2 per benchmark (60), let LFM3 answer without caring whether answers are right,
translate inputs and outputs to Turkish with another AI, SFT the Turkish CPT model
(`cbarkinozer/LFM3-1.7B-Turkish-CPT`) on the 300 rows, then compare Turkish and
benchmark scores against the base.

Agreed: self-distillation without correctness filtering is a valid preservation
arm (the targets stay in the model's own distribution). Revisions after review:

1. **Benchmarks are not usable as one-shot prompt sources.** The card table has 29
   rows but about 25 distinct benchmarks. Most agent, tool-use and agentic-coding
   ones (WebArena, SWE-bench x2, Terminal-Bench, tau3, MCP-Atlas, LiveClaw,
   Claw-Eval, BrowseComp-Plus, EnterpriseOps, AutomationBench, ToolSandbox) are
   multi-turn tasks in live environments or repos; RULER and AA-LCR are very long
   documents. Roughly 10-12 are single-prompt text: IFEval, IFBench, IFStruct,
   Multi-IF, GPQA, HLE (no tools), AA-Omniscience, LiveCodeBench, BFCL single-turn.
2. **Do not train on benchmark items.** GPQA and HLE are believed to carry canary
   strings asking not to be used for training (verify before any use). Training on
   them also consumes the benchmarks we need as an unbiased guard. Sample the same
   prompt types from training-split sources instead: GSM8K train, MBPP train, public
   function-calling sets with gold calls, IFEval-style synthetic constraint prompts.
   Use the real benchmarks for evaluation only.
3. **60 hold-out rows cannot detect "not degraded too much".** At n=60 one score has
   a 95% interval of about +-12 points (2 items per benchmark is worse). Run the
   guard on full benchmarks or large subsets with the model-card sampling presets
   (IFEval 541 items; BFCL and LiveCodeBench subsets). The 60 translated items are
   a sanity check on Turkish answers only.
4. **300 rows test preservation, they do not teach Turkish.** Turkish ability comes
   from the CPT model (grammar about 80% in our tests) and the translator's style.
   The pilot answers one question: does SFT stop breaking thinking-off arithmetic
   and tool calling? Decent Turkish answering is the job of the scale-up phases.
5. **Translate only the final answer; keep the thinking trace in the model's own
   English** (reasoning in the user's language costs accuracy, Qi et al. 2025).
   Targets sampled from the original LFM3 are off-policy for the CPT model: that
   pulls the CPT model back toward the original's behavior (intended), but run the
   same rows on the original model too to see whether CPT helps or hurts.

Revised pilot (about $2-3): about 300 prompts across the usable categories plus
about 50 plain Turkish chat/writing prompts (benchmark-style prompts alone teach no
Turkish conversation). Targets = original LFM3's own answers, final answer
translated by writer AI and checked by a different-family fixer AI.
Arm A unfiltered (owner proposal); arm B keeps only answers that pass automatic
checks where a check exists. Starting checkpoints: original LFM3 and the Turkish CPT
model (four short runs). Pass condition: English guard, thinking-off arithmetic and
tool calling within noise of base; Turkish no worse than exp014.

## 4. Evaluation v2 (freeze before any training; never train on it)

- **Paired bilingual verifiable set, about 300 items, each in EN and TR:** math
  (`malhajar/gsm8k_tr-v0.2` test items with the matching English GSM8K test item;
  the card claims human verification but only 1104 of 1319 items pass our
  invariant check and several answers differ, so only clean pairs are used),
  tool calls (BFCL gold), code (unit tests, Turkish prompt), checkable
  instructions. Built so far: [eval-v2](eval-v2/README.md) (math 152, symbolic 60,
  tool calls 80 pairs). Report EN accuracy (preservation), TR accuracy,
  TR-EN gap, answer-language rate, thinking-closure rate, length, EOS.
- **Turkish grammar without generation:** TurBLiMP minimal pairs (as in Liquid's
  CPT notebook) and Wiki/web NLL.
- **Preservation guard from the model card:** IFEval, BFCL subset, a code subset
  (LiveCodeBench or HumanEval+), GPQA Diamond, a math set; card sampling presets.
- **Human review only for finalists:** about 30 generative Turkish items, blind,
  scored for correctness and naturalness separately from preference.
- Statistics: paired McNemar/bootstrap on items; at least 3 sampling seeds for
  finalists; a change counts only if the interval excludes zero.

## 5. Threats to validity and how each is handled

| Threat | Handling |
|---|---|
| Tiny, consumed dev packets | Eval v2 with ~300 paired items; old packets stay diagnostic only |
| Preference treated as accuracy | Verifiable accuracy first; review scores correctness and naturalness separately |
| Decoding mismatch (greedy rp1.15 vs card presets, thinking on/off) | Card presets per task; report both thinking modes |
| Single seed | 3 sampling seeds for finalists; second training seed for the winner |
| Contamination (GSM8K-TR test, Cetvel, old packets, teacher paraphrases) | Train only on train splits; n-gram and embedding dedupe against every eval set |
| Lenient or brittle answer extraction (last-number screen errors documented) | Robust extractor + manual audit of every extractor/judge disagreement |
| Selection bias of self-distillation (easy items survive) | Report drop rate per category; the goal is preservation, not new skill |
| Rendering drift (writer changes content) | Invariant checks + fixer equivalence check + owner spot check of 100 rows |
| Translationese | Native Turkish prompts first; owner rates naturalness specifically |
| Language-ID errors on code/numbers | Strip code blocks and numbers before language ID |
| Tool-call format drift | Render through the native chat template; parse every tool row; BFCL subset in guard |
| English thinking leaking into answers | Measure answer-language rate; gate at 98%+ Turkish when Turkish is requested |
| Confounded comparisons | Pilot changes only the target source vs exp014 (same prompts, recipe, steps, order) |
| Truncation from Turkish token fertility | Measure tokens/word; assert zero truncation (existing audit) |
| Provider terms for generated data | Check terms before generation; keep restricted until resolved |

## 6. To-do list (gated)

Phase 0: evaluation (CPU + about 3 GPU hours)
- [ ] Build eval v2 (paired EN/TR verifiable set, TurBLiMP, guard subset); freeze hashes.
      Done 2026-11-21 (CPU-verified, [eval-v2](eval-v2/README.md)): math, symbolic and tool-call
      packets, scorer, summary/compare script, vLLM runner (not yet run on a GPU).
      Left: Turkish code and checkable-instruction families, English guard set, owner spot check
      of the Turkish items, freeze.json.
- [ ] Run it on base, CPT-100M, exp014, exp015 with card presets, both thinking modes.
- [ ] Gate: base reproduces known behavior (symbolic 8/8; TR-EN gap visible).

Phase 1: pilot `exp-016-self-distill-targets` (about $2)
- [ ] Same 160 groups, same four directions as exp014; replace only the targets
      with self-distilled ones (section 3). Same LoRA r32/alpha64, LR 1e-4, mask,
      order, steps as exp014.
- [ ] Record per-category verified-sample rate (also a direct EN ability measure).
- [ ] Gate to scale: thinking-off arithmetic and EN guard within noise of base;
      TR accuracy and TurBLiMP not worse than exp014; answer language Turkish when asked.
- [ ] Optional arm B only if A passes but the TR-EN gap stays: thinking starts with
      a one-line English restatement of the Turkish problem.

Phase 2: data engine (API + about 2 GPU hours)
- [ ] Choose writer and fixer from different model families; confirm training-use terms.
- [ ] Build invariant checkers (numbers, entities, code, JSON, units, language ID).
- [ ] 50-item dry run across all categories; owner reads all 50; fix prompts.
- [ ] Generate 2k, then 6k groups; owner spot-checks 100 random + 30 lowest-scored rows per batch.

Phase 3: scale ladder (about $5)
- [ ] 2k -> 6k -> 15k rows with the pilot recipe; stop when TR gains flatten or the guard drops.
- [ ] LoRA-scale sweep 0.5-1.0 on the best checkpoint (no training).

Phase 4: escalations, only if a named gate fails
- [ ] Turkish fluency plateaus: CPT on `LFM3-1.7B-Base` (Turkish + English/code
      replay, LoRA r64-128, optionally embeddings), then transplant the delta onto
      the instruct model (Chat Vector / ElChat); about $5 per 300M tokens.
- [ ] Guard drops after scaling: on-policy distillation (TRL GKD) with the original
      LFM3 as teacher on English/tool/math prompts.
- [ ] Math still weak in Turkish: layer swapping between the Turkish adapter and the
      original model (untested on LFM3's hybrid conv/attention stack).
- [ ] GRPO with verifiable rewards last.

Phase 5: final
- [ ] Fresh holdout, 3 seeds, guard, blind owner review; write-up and Medium article.

## 7. Budget (estimates, not measured)

| Item | 4090 hours | Cost |
|---|---:|---:|
| Eval v2 baselines (4 models, 2 modes) | 3 | $1.2 |
| Pilot generation + training + eval | 3 | $1.2 |
| Data engine self-generation (6k-15k groups, k=4) | 2-4 | $1.6 |
| Scale ladder (3 runs + evals) | 8 | $3.2 |
| Optional base CPT 300M tokens | 12 | $4.8 |
| Optional on-policy distillation | 5 | $2.0 |
| Total GPU | 20-35 | $8-14 |

API cost for writing and fixing about 15k answers depends on the chosen models and
was not priced here.

## 8. References

- SDRRL, self-distillation from resource-rich languages: https://aclanthology.org/2024.acl-long.603
- SDFT, self-distillation bridges distribution gap: https://aclanthology.org/2024.acl-long.58
- Native vs translated instruction data: https://arxiv.org/abs/2406.12822
- Thinking in the user's language costs accuracy: https://aclanthology.org/2025.findings-emnlp.1103
- Spurious forgetting: https://arxiv.org/abs/2501.13453
- Chat Vector: https://aclanthology.org/2024.acl-long.590 ; ElChat: https://arxiv.org/abs/2412.11704
- On-policy distillation (Thinking Machines): https://www.thinkingmachines.ai/blog/on-policy-distillation/
- Layer swapping: https://arxiv.org/abs/2410.01335
- LoRA learns less and forgets less: https://arxiv.org/abs/2405.09673
- Liquid LFM3 model card and cookbook (CPT Turkish notebook): https://huggingface.co/LiquidAI/LFM3-1.7B
- Community precedents: https://huggingface.co/SkyAsl/LFM2.5-1.2B-TR-Base (0.8B tokens, LoRA r128 on base),
  https://huggingface.co/bedop/LFM3-1.7B-Turkish (LoRA CPT)
- Turkish GSM8K: https://huggingface.co/datasets/malhajar/gsm8k_tr-v0.2 ; Cetvel: https://arxiv.org/abs/2508.16431
