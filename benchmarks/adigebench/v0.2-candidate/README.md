# AdygheBench v0.2-candidate

This is the curated development revision of
[`v0.1-candidate`](../v0.1-candidate/README.md). It has **188 items**.

The change is intentionally narrow: remove objectively invalid or duplicate
evidence without making any unsupported linguistic correction. The complete
row-by-row rationale is in `curation-decisions.json`.

## What changed from v0.1

- Removed 9 duplicate-input rows while retaining one canonical item per
  duplicate group.
- Removed IDs 107–108: “Can you speak Adyghe?” legitimately permits both a
  yes and a no answer; it cannot have one reference answer without additional
  scenario context.
- Removed ID 109: its prompt asks whether the speaker has eaten, but the
  supplied reference is the unrelated response “I can.”
- Removed IDs 191–195, which only repeat existing lexical translation prompts.

The task is still a **candidate diagnostic**. A native reviewer must validate
the remaining references and define acceptable alternatives before reportable
use. The material is user-authored and may be used for training; consequently,
this benchmark measures curriculum mastery after such training, not unseen-data
generalization.

## Build

```powershell
python scripts/evaluation/build_adigebench_v01.py `
  --source 'C:\Users\cbark\Downloads\adige-bench.txt' `
  --related-source 'C:\Users\cbark\Downloads\adige data.txt' `
  --version v0.2-candidate `
  --exclude-source-row-ids 104,107,108,109,136,137,145,191,192,193,194,195 `
  --output-jsonl benchmarks/adigebench/v0.2-candidate/adigebench-v0.2.jsonl `
  --audit-json benchmarks/adigebench/v0.2-candidate/audit.json
```

Use this revision, not v0.1, for the first baseline once native review is
complete.
