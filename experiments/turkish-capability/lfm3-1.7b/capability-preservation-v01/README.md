# Capability preservation v01

Prepared 2026-11-19 for the owner-authorized next GPU experiments. Data only;
no training, inference, GPU access, publication, or existing-file changes.
Hypothesis: a small verified bilingual supplement may reduce arithmetic and
English retention regressions while preserving useful Turkish behavior.

- `train.jsonl`: 80 fresh rows, 40 Turkish and 40 English; 40 worked-solution
  reasoning rows (five structures, four instances per language), 40 individually
  authored general-language rows. No translated copies of historical items.
- `eval-prompts.jsonl`: 32 fresh evaluation-only prompts, 16 per language;
  no assistant answers. Eight numeric/logic and eight general tasks per language.
- `eval-references.jsonl`: separate references/rubrics; never send to model or
  include in training. Freeze this holdout for one final comparison; using it to
  choose checkpoints or recipes consumes it as development data.
- `verification-cases.json`: 56 executable arithmetic/logic checks, including
  exhaustive search, cell counting, exact fractions, sets and truth tables.
- `validation.json`, `overlap-review.json`, `protected-inputs.json`, `manifest.json`:
  validation, nearest historical prompts, read-only input hashes and output hashes.

Schema matches all top-level active corrections-02 train keys. Native reasoning
is a separate `worked_solution` string, never invented reasoning tags. Assistant
targets are concise final answers. The future runner must apply the native chat
template and explicitly decide reasoning supervision; attaching this metadata
does not itself enable reasoning loss. Do not silently change the existing loss
policy. General rows keep null worked_solution/reasoning_language.

The builder contains all authored source text and deterministic templates. No API,
external corpus or prior evaluation is used to produce targets. Historical local
JSON/JSONL is scanned afterward only for leakage; its content is not a generator
input. Provenance: OpenAI Codex assistant session, exact backend revision and
sampling settings unavailable; Python instantiation deterministic, no RNG.
Owner authorization covers private research data creation/use for all three
experiments (NEXT-GPU-AUTHORIZATION.md); this packet does not authorize publishing
or resolve broader provider licensing terms. No third-party source is claimed.

Training reasoning families: signed repeated change, indexed progression,
sum/difference equations, reversed operations, transitive numeric ordering.
Holdout reasoning families: synchronization/LCM, inner border area, draws without
replacement, median, inclusion-exclusion, ceiling capacity, midnight rollover,
exclusive constraints with multiple satisfying assignments. These are absent
from this supplement's training templates, but not necessarily from historical
training or model pretraining. New train/eval arithmetic facts differ by language.
General holdout tasks emphasize ambiguity, scope, evidence versus causation,
titles, register and error detection rather than repeating new training prompts.

This is limited synthetic template generalization: 80 rows are not 80 independent
reasoning structures. Eight holdout reasoning structures each appear in both
languages; report 32 item outcomes plus family/language breakdowns, not 32 fully
independent families. Agent-authored prose has no independent owner adjudication.
Automated overlap screens do not prove semantic or cross-lingual independence.
Common small constants and generic instructions can recur; no claim of globally
disjoint individual numbers is made. Protected-input inventory scopes the local
scan; external benchmark contents and unstructured text files are not exhaustive.

Reproduce/verify (CPU, standard library only):
`python scripts/data/build_lfm3_capability_preservation.py`
Existing files must match byte-for-byte; the builder refuses to overwrite.
Freeze artifacts before baseline. If the repository's protected inputs change,
preserve this packet and produce a separately versioned audit rather than editing
its frozen inventory. Character lengths are reported; model token lengths are
not inferred. Before actual training, audit native-template labels, lengths,
EOT and truncation on the exact combined dataset and pin its order/token budget.
This supplement is not a replacement for the active 640-row dataset, and no
mixing ratio, run config, step count or checkpoint-selection rule is changed here.

For future inference use separate conversations, no reference/few-shot leakage,
and identical pinned model/template/backend/generation conditions per comparison.
Keep thinking-on/off separate cohorts. Score correctness, constraint/format and
language compliance, naturalness, and stopping separately; accept equivalent
prose rather than exact-string matching. Compare against untouched LFM3 and the
existing candidate controls. Preserve raw outputs, IDs, finish reasons and configs.
Predeclare acceptable regression budgets before observing these holdout results.
