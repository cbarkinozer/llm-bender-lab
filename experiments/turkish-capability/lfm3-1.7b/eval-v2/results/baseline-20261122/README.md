# Eval v2 baselines, 2026-11-22 (seed 3407, model-card presets, one run per cell)

RTX 4090 on Vast, vLLM 0.34.0rc1.dev251, torch 2.14.0+cu130, transformers 5.20.2. Pinned base
`LiquidAI/LFM3-1.7B@0dc4268`. CPT = `cbarkinozer/LFM3-1.7B-Turkish-CPT@6f213ec` merged into the base (weight sha256
reproduced the historical merge exactly: `f4562118…`). Single seed: treat differences under about 5-9 points as noise.
exp014 and exp015 baselines were not run (adapter upload from the owner's machine was too slow).

Accuracy (n: math 152, symbolic 60, tool calls 80 per language):

| Cell | base off | base on | CPT off | CPT on |
|---|---:|---:|---:|---:|
| math EN | 0.895 | 0.954 | 0.572 | 0.928 |
| math TR | 0.395 | 0.717 | 0.033 | 0.632 |
| symbolic EN | 0.967 | 0.967 | 0.500 | 1.000 |
| symbolic TR | 0.967 | 0.983 | 0.233 | 0.950 |
| tool calls EN | 0.950 | 0.950 | 0.063 | 0.913 |
| tool calls TR | 0.738 | 0.825 | 0.000 | 0.750 |

## Findings

- **The Turkish gap is real and large in the base model.** Math EN to TR: 0.895 to 0.395 thinking off (paired
  interval -0.58 to -0.42), 0.954 to 0.717 thinking on. Tool calls: 0.95 to 0.74 off. Symbolic arithmetic shows no gap
  (the prompt is language-neutral), so the gap is reading Turkish word problems, not arithmetic.
- **Base Turkish math with thinking off often fails to stop**: 31% of rows hit the 2048-token cap (rambling and
  self-doubt loops), versus 7% in English.
- **The published CPT adapter is unusable with thinking off.** It continues text in Turkish as a document
  (ignores the task, no EOS in 36-54% of tool rows): tool calls 0.95 to 0.06, symbolic 0.97 to 0.50, all with
  paired intervals far below zero. With thinking on most of the damage disappears (differences -0.03 to -0.09,
  only math TR is nominally significant, p=0.04), consistent with earlier findings that CPT on the post-trained
  checkpoint hurts chat behavior.
- Thinking on is better than off for the base model everywhere, most of all for Turkish math (+0.32).
- Tool-call output is the template's XML format (20 of 20 smoke rows parsed); scorer and runner worked first try.

Files: `<model>-think-<mode>/summary.json` and `run-manifest.json` (raw answers and per-item scores stay in the
ignored `runs-local/`), `compare-cpt-vs-base-think-<mode>.json`, `merge-receipt-cpt.json`.

## Self-distilled runs and TurBLiMP (added later the same day)

Arms A, B, C of [exp-016](../../../exp-016-self-distill-targets/README.md) were evaluated the same way; their summaries and
compare files sit beside the baselines, and `turblimp/<model>.json` holds the grammar scores (macro accuracy, frozen
1600-pair subset): base .718, CPT .869, A .718, B (CPT parent) .868, C .708. The CPT model's grammar gain survives the
self-distilled SFT while its chat behavior is repaired; Turkish math accuracy does not improve in any arm.
