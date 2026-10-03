# exp-013-targeted-coverage-sft (C)

## Status

SFT and primary inference completed; human comparison pending. All12 reviews
exported:7 accept,5 rewrite, plus2 explicitly user-authorized QA corrections.
Active config-reviewed-v1.yaml, data-reviewed-v1 and training-preflight-v1.
`config.yaml` remains deliberately blocked draft history, not the active recipe.
Training4epochs/40steps;20/20 native EOS; backup verified locally. Do not use draft files.
See [GPU-RUN-NOTES.md](GPU-RUN-NOTES.md) for execution, waived gates and outcomes.

[Review the12 shared C/D candidates](http://127.0.0.1:6900/dataset/c0dc183f-e552-4a7d-9267-08211b88df94/annotation-mode?page=1&status=pending).
Use accept, or rewrite with the complete corrected answer, or reject with notes.
Review completed; no further candidate annotations required for either experiment.

## Goal and hypothesis

Test whether a narrow intervention fixes precision/unsupported-reasoning errors
without sacrificing A's useful explanation, natural Turkish and interaction.
Neither success nor combining all A/B strengths is assumed.
Parent: exp011 duration-ablation (saved A); fresh pinned base, not A's weights.

## What changed

Retain68 original reviewed A rows in their original positions. Replace12:
me-001/002, me-011/013/015/016, me-021/022/024/026, me-033/034.
These are2 grammar,4 extraction,4 numeric/entity,2 summary rows. Keep EVERY
original training row above me-040, including all explanation, clarification,
groundedness, Turkish precision, non-anthropomorphism and consistency examples.

New12:4 exact fact/entity answers,4 evidence-bounded reasoning/explanation
answers,2 Turkish grammar/word-meaning checks,2 condition/uncertainty rewrites.
They are project-agent-authored drafts in distinct fictional settings, NOT
summaries of generated base answers and NOT validation paraphrases.
See candidate_specs.py for the authoring brief and preserved source metadata.

## Data and leakage

80 train / unchanged20 development validation. Original source hashes verified.
All68 retained rows also have identical tokenized representation to A.
Checks compare new12 with original80/20,348 historical benchmark entries,
3500 historical training inventory entries (not unique independent rows),
and B's24 new entries. No exact matches or near flags detected. Thresholds:
0.60 for current validation,0.78 for other corpora/new-new comparisons.
Scenario/provenance inspection is documented in data-draft-v2/leakage-report.json.
Lexical checks and manual inspection cannot prove universal semantic independence.

Draft supervised tokens:5578/epoch versus A5384 (+3.60%); recompute after review.
Final reviewed/QA-corrected tokens5653/epoch versus A5384 (+5.00%).
Changing composition also changes token exposure, so this is not an isolated
data-quality causal estimate. Maximum draft train sequence514 tokens; no
truncation at1024. Native EOS supervised; context including empty-think prefix masked.

## Training and evaluation

Same pinned model, tokenizer, LR1e-4, BF16 rank/alpha16/16, modules, batch1×8,
seed3407,1024 sequence, AdamW8bit, cosine/warmup2 as A. Four epochs/40steps.
Final scheduled checkpoint preselected, no validation-based best selection.
Shared exp009 trainer/preprocessing and bounded HF/Unsloth inference; no vLLM.
No earlier gate waiver inherited. New actual-batch/environment/W&B and
smoke/reload/tiny-overfit gates or explicit scoped user waiver required.

Compare saved A/C/D on the same20; see [EVALUATION.md](EVALUATION.md).
me-089 reference is disputed and untouched, with separately reported sensitivity.
No training data contains development prompts or their paraphrases.

## Local workflow

CPU environment used: C:/Temp/llm-bender-exp009-preflight/Scripts/python.exe.
Argilla SDK environment: exp001 annotation/argilla/.venv/Scripts/python.exe.

1. `prepare_next_pair.py`: immutable drafts, blocked C/D configs, CPU preflight.
2. `import_review.py`: create/read-back12; existing fields/reviews never overwritten.
3. User submits12 accept/rewrite decisions, resolves any rejected prompts.
4. `export_review.py`: read-only Argilla export; fail unless all12 reviewed;
   re-audit/tokenize, freeze one shared data-reviewed-v1 and C/D reviewed configs.
5. Commit reviewed provenance, obtain GPU, pass required checks, run C then D
   independently, infer, download/verify all artifacts, prepare A/C/D comparison.

The historical shared tokenizer's draft report says “human approval for B”;
for this reused helper it means the12 C/D candidates. pair-preparation-report-v2.json
is authoritative on the new pair's status. candidate-mask-inspection-v2.json
contains every new row's actual rendered input and supervised tokens.

## Results and lessons

Execution complete: mean training loss1.1909237187,153.696seconds; final adapter
generated20/20 native EOS. User explicitly waived smoke/tiny-overfit/pre-SFT
diagnostic reload for this pair; actual masks/W&B passed and post-SFT reload
verified.129 indexed backup files verified. No quality improvement claim yet.
[Review desired/A/C/D](http://127.0.0.1:6900/dataset/e3b691cb-79fc-4bd8-a358-39f9a23770b5/annotation-mode?page=1&status=pending).

The preparation history below is preserved chronologically, not current run status.

No model-quality result yet. Ten CPU tests passed; exporter correctly
refused unreviewed tc-001, producing no approved data or reviewed configs.
Preparation found a namesake-module import collision from older helpers changing
sys.path; restoring this experiment first fixed it. Regression test added.
No frozen old data, references, reviews or configs modified.

Final freeze: data-reviewed-v1 contains raw12 submissions, original reviewed
candidates, approved candidates, two before/after QA diffs and the user's
hash-bound conversational authority. tc-010 lexical-trap hint removed; tc-005
categorical cable diagnosis softened. Other10 reviewed candidates unchanged.
All68 original A rows and20 validation rows remain unchanged. All12 CPU tests
pass. verify_ready.py confirms C/D byte-identical data/tokenization and distinct
4/6epoch configs, all artifact hashes, native EOS/masks and original provenance.
[GPU-HANDOFF.md](GPU-HANDOFF.md) records next launch and recovery requirements.

Before handoff, draft v2 corrected tc-010 from ambiguous “doktora başvurmuş”
to “doktora programına başvurmuş.” Doctor consultation and doctoral education
must not be conflated without context. Targets and other11 prompts unchanged.
The original draft/source and original12-row queue are preserved, not overwritten.
Only the v2 queue linked above is active; export reads annotation-link-v2.json.
