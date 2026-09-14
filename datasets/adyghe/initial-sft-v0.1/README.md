# Initial Adyghe SFT candidates v0.1

`initial-training-data.csv` is the requested combined, model-neutral CSV.
It combines the cleaned Adyghe--English Wiktionary extraction and the supplied
`adige data.txt` records. It has explicit input/target/POS/variant columns and
an explicit split per source record.

The CSV is not directly tokenized training text. A later Qwen-specific builder
will render `input_text` and `target_text` through the pinned chat template.

## Leakage policy

`adige-bench.txt` is derived from `adige data.txt`. Therefore all
user-authored rows are included for inspection but assigned
`excluded_benchmark_parent`, rather than silently being used to train against
their own final diagnostic. Exact Wiktionary overlaps are likewise excluded.

The eligible rows use a deterministic, stratified 80/10/10 train/validation/
development-test split. The development test is not the final benchmark.

`adigebench-v0.2-candidate.csv` is the sole initial diagnostic CSV,
with 188 curated records. Reading items retain their required passage in the
`context` column. It is not used during optimization.

## Rebuild

```powershell
python scripts/datasets/build_adyghe_initial_csv.py `
  --wiktionary-source datasets/adyghe/adyghe-english-wiktionary-v0.1/raw-source.tsv `
  --user-source "C:\Users\cbark\Downloads\adige data.txt" `
  --benchmark-source "C:\Users\cbark\Downloads\adige-bench.txt" `
  --training-csv datasets/adyghe/initial-sft-v0.1/initial-training-data.csv `
  --benchmark-csv benchmarks/adigebench/v0.2-candidate/adigebench-v0.2-candidate.csv `
  --audit-json datasets/adyghe/initial-sft-v0.1/audit.json
```
