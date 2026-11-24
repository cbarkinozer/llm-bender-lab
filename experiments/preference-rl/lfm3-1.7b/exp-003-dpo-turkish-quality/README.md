# exp-003-dpo-turkish-quality

## Status

`data built, not trained`. Design written 2026-11-24. Sampling ran on a pod the same day (exp-021 and the original model, 4 answers per prompt; skills lane verified).
Turkish repairs, three rounds (AI-assisted edits under the owner's supervision, labelled synthetic):

- Round 1 took the most severe answer per prompt and produced mostly rewrites (chosen about half as long as rejected), which would teach "answer shorter". Only the 26 minimal repairs and 49 rewrites within a 0.75 to 1.33 length band are kept.
- Rounds 2 and 3 took the mildest flagged answer that ended properly, then the next mildest. Repairs stay under 25% of the words and about 1.0x the length. About 80% of the offered answers were dropped as wrong at the task level (the detectors do not see wrong content).
- Result: 130 Turkish pairs (81 minimal, 49 light rewrites; 10 from template prompts, 120 from Atlas prompts) and 173 skills pairs. The mix caps each skills cell at 30: 225 pairs (130 Turkish, 95 skills).
- The Turkish lane is below the 200-pair target, and IFEval-like (5) and tool (3) pairs are thin, so the IFEval guard is the most at risk. Treat the first run as a pilot.
- The training runner is not generalised yet and nothing was trained.

## Goal

Improve the Turkish accuracy of the published Turkish SFT model (`cbarkinozer/LFM3-1.7B-Turkish-SFT`, exp-021) with DPO **without breaking
the fundamental skills**: instruction following (IFEval), code (HumanEval), English ability and math. The training code is the official recipe
of the Liquid notebook (LoRA, sigmoid DPO loss plus an SFT term, its hyperparameters unchanged) and the data has the notebook's format
(`prompt`, `chosen`, `rejected`, `chat_template_kwargs`), with two lanes in one file:

- **Turkish lane** (what improves): **rejected** is exp-021's own bad answer, **chosen** is the same answer repaired with as little change as
  possible (written by an AI assistant or the owner, validated by script). Small differences teach DPO exactly what was wrong and keep length and
  wording close to what the model already writes.
- **Skills lane** (what must not break): **rejected** is exp-021's own wrong answer to a math, code, tool-call or countable-constraint prompt,
  **chosen** is its own verified right answer to the same prompt. Labels come from checkers, no editor involved, and both sides are the model's
  own text, so these pairs pull the model towards what it can already do instead of away from it.

This changes two things against a plain Turkish DPO (the Turkish lane and the skills lane, plus two starting points, see below); it is a
learning experiment, so the arms are reported separately and no single hypothesis is claimed beyond the one below.

## Two arms, one pair set

The owner wants to know which start is better, so the same pairs train two policies (decided 2026-11-24):

- **arm-sft**: DPO over exp-021 (original model + Turkish CPT + SFT).
- **arm-base**: DPO over the original `LiquidAI/LFM3-1.7B` (no Turkish training).

Pairs are built from exp-021's wrong answers (the model we want to improve); the base arm sees them as off-policy data, which is part of
what the comparison measures. The pod job also samples the original model on the same prompts: that gives its error rates on these prompts
and keeps the option of a second pair set made from its own wrong answers. Reading the result: exp-021 against exp-021 + DPO, base against
base + DPO, and the two DPO models against each other. Base + DPO is DPO alone on a model that had no Turkish SFT, so it will start much
lower; "better" means the final quality, and the gain each arm gets from the same data is reported next to it.

## Hypothesis

A few hundred repaired Turkish pairs lower the share of answers with invented words, unfinished endings and broken countable constraints, and
an equal number of the model's own right-against-wrong skill pairs keeps IFEval, HumanEval, English and math within their noise.

## Parent Experiment

`exp-021-sft-core-pack-v2` (turkish-capability). Numbering of this line restarts at `exp-000-baseline`; this one follows `exp-002-grpo-phone-tools`.

## What Changed

DPO with the pairs of this experiment on two starting points (arm-sft, arm-base). Nothing else.

## Weaknesses of exp-021 that this data targets

All numbers come from the exp-021 evaluation (`experiments/turkish-capability/lfm3-1.7b/exp-021-sft-core-pack-v2/README.md` and its local
results). AI ratings are not human review. "Detectable" means a script can flag it; the rest needs the editor's judgment.

| # | Weakness | Evidence for exp-021 | Detectable | In this data |
|---|---|---|---|---|
| 1 | Invented or wrongly suffixed words | 1.45 flagged words per writing answer (original 3.27); examples: kutuplağa, yaşılan, evesiz, donatırır, erterleyebilir, dikkatınızı | partly (Zeyrek and word frequency; misses valid-looking wrong forms) | yes |
| 2 | Answer does not do the task | task correctness 0.39 (only 4 of 40 judged fully correct); wrote advice about an e-mail instead of the e-mail, explained "faiz" wrongly | no | yes (editor) |
| 3 | Wrong terms and facts | "İstihdam fonu", "değer katsayısı" for investment fund and return; "keçi kedi" in a story | no | yes (editor) |
| 4 | English leaking into Turkish | "Meeting, Wednesday'te" in a translation; "Demand (Isı)" | yes | yes |
| 5 | Answers that never end | 2 of 40 writing answers hit the 800-token cap (5%); 43 of 800 math samples (thinking on, EN and TR) had no end token | yes | yes |
| 6 | Countable constraints broken | 8 of 12 writing constraints met (67%); IFEval strict without thinking 69.9 (base 73.0) | yes | yes |
| 7 | Unnatural phrasing | naturalness 3.1 of 5; only 25% rated 4 or 5, 20% rated 1 or 2 | no | yes (editor) |
| 8 | Weak grammar phenomena | TurBLiMP: ellipsis 28%, relative clauses 69%, transitive argument structure 73% (macro 85.9) | benchmark | **no**: eval data, never trained on |
| 9 | Reading gap | Belebele TR 48.7 (EN 70.0); diagnostic cell D 76.6 against 94.6 in English | benchmark | **no**: eval data, and not an answer-editing problem |
| 10 | Turkish math | final test TR 78.2 against EN 92.7 (seed spread up to 7 points) | yes (answer check) | skills lane (own right against own wrong answers, no editor) |

Weaknesses 8 and 9 are real but cannot be fixed with edited answers here: the benchmarks are our evaluation sets. Math (10) has automatic right and
wrong answers, so it rides in the skills lane, which is there to protect skills first and may lift Turkish math as a side effect (reported, not claimed).

## Base Model

arm-sft: policy and reference are exp-021 merged weights, `cbarkinozer/LFM3-1.7B-Turkish-SFT` at commit `6e4f0b7658b115a28da971f82ff4009f63bed612` (also recorded in the sampling manifest), bfloat16.
arm-base: `LiquidAI/LFM3-1.7B` revision `0dc4268b561499c648c7ba7c9466bf3d8d01517a`, bfloat16. Both arms use its tokenizer and chat template. Thinking is set per row: off for the Turkish writing pairs and the English constraint prompts (as in the notebook), as sampled for math, code and tool rows.

## Dataset

Pipeline (each step is a script; every output carries hashes):

1. `scripts/datasets/tr_dpo_prompts.py build` makes `data/prompts-tr-dpo.jsonl`: 526 prompts, none seen by exp-021, none a near duplicate of
   the 40 writing-probe prompts (checked, fails loudly).
   - 443 Turkce Atlas prompts (MIT; 224 with countable constraints, 203 plain, 16 with a long context) whose answers exp-021 was not trained on.
     Atlas prompts are workplace-flavoured, so they do not cover everyday writing.
   - 83 hand-written everyday prompts for the weak categories Atlas lacks: explain 15, e-mail 14, rewrite 14, creative 12, translate 14,
     countable constraints 14. Their style matches the writing probe, their topics do not.
2. `scripts/training/sample_tr_dpo_candidates.py` (pod, vLLM): 4 answers per prompt from exp-021 (and the same from the original model, `full-base`), thinking off. Sample 0 uses the model card
   preset (temperature 0.1, the usual behaviour), samples 1 to 3 temperature 0.7. Answers that hit the 800-token cap are kept.
3. `scripts/datasets/tr_dpo_flags.py flag`: detectors per answer (cut at the cap, empty, English reply, repetition, constraint, unknown
   words, English words) with a severity; also the weakness profile of exp-021 on these prompts.
4. `scripts/datasets/tr_dpo_flags.py worksheet`: the editing worksheet. Per prompt the most severe flagged answer; all 83 everyday prompts
   are kept, Atlas rows fill up to 300 rows, most severe first. An AI assistant edits it following `EDITING-GUIDE.md`.
5. `scripts/datasets/tr_dpo_flags.py validate` and `pairs`: an edit is usable only if it changes at most 25% of the words (the minimal kind),
   keeps the length within 85 to 115% (waived when the model answer was cut off), passes the countable constraints, has no flagged or
   English words left, and ends like a finished answer. The pairs are labelled `synthetic`.

A seeded 15% of the Turkish prompts (by hash of the prompt id) is held out before editing and is used only for measurement (flags before and
after). Pairs with a cut-off rejected answer need runner support: TRL appends the end token to every assistant message, which would hide
the missing ending, so those pairs are passed as prompt and completion text without the end token (to build when the data exists).

**Skills lane** (automatic labels, same model, no editor):

6. `scripts/datasets/tr_dpo_skill_prompts.py build` makes `data/prompts-skills-dpo.jsonl`, 920 prompts from the SFT core pack (already
   leakage-audited against our eval sets; GSM8K test, HumanEval and IFEval are not used): Turkish math 587, English math 124, code 143, tool
   calls 18, and 48 English prompts with countable constraints ("at most 40 words", "exactly 4 bullets") written here. Only prompts where the
   original model was not right in all 4 samples are taken, because a wrong answer is likely there.
7. Pod: the existing `generate_lfm3_sft_samples.py` (4 answers per prompt from exp-021, its model-card presets, thinking as in the pack) and
   `verify_lfm3_sft_samples.py` (math number, MBPP tests executed on the pod, tool-call match, constraint check).
8. `scripts/datasets/tr_dpo_skill_pairs.py build`: per prompt one pair (verified answer, wrong answer) with the closest lengths, so length
   is no shortcut; wrong answers that were cut at the token budget or never closed their thinking are not used as rejected (see the end-token
   note above); the pair must fit 3,000 tokens (the example trains at 3,072; a first check on the original model's old samples loses 131 of 719
   prompts to this); at most 100 pairs per category and language. A dry run on the original model's existing samples gave 206 pairs (Turkish
   math 100, English math 49, code 47, tool 10), so the lane is feasible. Thinking is kept in the assistant message like the SFT pack, and each row
   carries `chat_template_kwargs` (thinking on for math, tool and code rows that were sampled with it).
9. `tr_dpo_skill_pairs.py mix` writes `pairs-dpo.jsonl`: all edited Turkish pairs plus skill pairs at a 1:1 ratio (`--skill-ratio`).

English general ability has no automatic checker here, so it is guarded by evaluation only (Belebele EN, IFEval, English math), not by pairs.

## Training Setup

The recipe of exp-001, which is the notebook's recipe, unchanged:

| Setting | Value |
|---|---|
| Method | LoRA DPO, sigmoid loss plus SFT loss on the chosen answers (weights 1 and 1) |
| Start | arm-sft: exp-021 merged weights; arm-base: the original model; reference = the same model with the adapter off |
| Data | `pairs-dpo.jsonl`: Turkish lane plus skills lane at 1:1 (the one change against exp-001 is the data and the per-row thinking flag) |
| LR / schedule | 2e-5, cosine, warmup 10% (the notebook's). Fallback, decided now: if a guard fails, rerun once at 5e-6, nothing else changed |
| beta | 0.1 |
| Batch / length | 2 x 8 accumulation, max length 3072 |
| Epochs | 1 (check `rewards/accuracies`, `rewards/margins` and `logps/chosen` in the log; lanes are logged separately in the manifest) |
| LoRA | r 16, alpha 32, dropout .05, attention, conv and MLP projections |
| Seed | 42 |

The runner `scripts/training/run_pref_dpo_grounded_qa.py` needs a generic option for a pairs file (with `tools`, `thinking` in assistant messages and per-row
`chat_template_kwargs`), a local model path and logging per lane; build that when the pairs exist, then the overfit check of the playbook before the run.

## Evaluation

Pre-registered before any run:

- **Held-out prompts** (about 80, never trained on): flagged answers (any detector), unknown-word types per answer, constraint pass, share
  of answers that end, mean words per answer. exp-021 is measured on the same prompts with the same sampler.
- **Writing probe** (40 native prompts, thinking off, same sampler and the same blind AI rating as exp-021): flagged words per answer,
  naturalness, task correctness, constraints, end-token rate. n = 40 resolves only large differences; it is reported, not gated.
- **Guards** (the skills the owner wants kept): IFEval strict (thinking on and off), HumanEval, English math and Turkish math (final test), Belebele EN and TR, TurBLiMP macro, diagnostic cell D, tool calls.
- Comparison models: exp-021, the original model, the two DPO arms against each other, and later `vngrs/Kumru-2B` on the Turkish items.

Success rules: (1) on the held-out prompts the share of flagged answers falls by at least a quarter, interval excluded from no change;
(2) mean words per answer stays within 15% of exp-021; (3) TurBLiMP within 2 points of 85.9, Belebele TR within 3 of 48.7, cell D within 3
of 76.6, IFEval strict within 3, HumanEval within 3, English math final test within 3 of 92.7; (4) no answer fully in English on the writing probe.
A failure of rule 2 or 3 means the DPO drifted; the answer then is a lower LR or fewer pairs, not a longer run.

## Results

Pending.

## Regressions

Pending.

## Conclusion

Pending.

## Limits (known before the run)

- The detectors see only part of the weaknesses (1, 4, 5, 6); 2, 3 and 7 depend on the editor's judgment, and the editor is an AI assistant
  whose Turkish is also imperfect. AI edits are labelled synthetic and are not human review.
- Rejected answers are sampled at 0.1 and 0.7; the model's behaviour at other settings is not covered.
- About 300 Turkish pairs plus about as many skill pairs is small. This is a hands-on learning run; claims need a seed repeat.
- The skill pairs come from prompts where the original model was weak, which is where its answers can be wrong, but they are the SFT core pack prompts that
  exp-021 trained on (with answers that were right). That is acceptable for preserving skills, and it means the skills lane says nothing about new problems.
- The English constraint prompts are 48 templates of our own with 4 constraint types; IFEval has many more. English general ability has no pairs.
- arm-base sees pairs made from another model's mistakes (off-policy); its result mixes the value of DPO with that mismatch.

## Pod steps (owner starts the pod; an estimated 1 to 2 hours on an RTX 4090, not measured: the skill prompts are thinking-on math and code)

    LFM3_POD_HOST=... LFM3_POD_PORT=... bash scripts/training/pod_tr_dpo_sampling.sh up      # sets up vLLM if missing, smokes, then Turkish prompts (exp-021 and original model) and the 920 skill prompts (exp-021, verified)
    ... status
    ... fetch experiments/preference-rl/lfm3-1.7b/exp-003-dpo-turkish-quality/results-local   # verified tarball, then the pod can be destroyed

Then locally (needs `pip install zeyrek wordfreq`): `tr_dpo_flags.py flag`, then `worksheet`; the editor works on `edit-worksheet.jsonl`. The skills lane needs no editing: `tr_dpo_skill_pairs.py build` on the fetched `skills/` files.

## Next Step

Pod: sample (steps 2 and 7), then flag and build the worksheet and the skill pairs locally. After editing: validate, build the Turkish pairs, mix, adapt the runner,
overfit check, then the arm-sft run, then arm-base with the same pairs.
