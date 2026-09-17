# Research Practice

This repo is run as independent, empirical LLM post-training research, not
curriculum consumption. The loop:

```
Question -> Literature -> Hypothesis -> Cheapest Experiment -> Baselines
   -> Metrics -> Results -> Interpretation -> Alternative Explanations
   -> Next Question
```

Niche: empirical post-training and model behavior, especially small/open
models. Good topics: multilingual reasoning, SFT/DPO/GRPO/CPT comparisons,
data quality, synthetic data, scaling effects, style-capability entanglement,
MoE adaptation, diffusion LMs, evaluation reliability.

## Weekly literature pass

Read HF Daily Papers weekly. Pick only a few. For each, write down:

- What they found.
- What evidence supports it.
- What they did not test.
- What question it creates for us.

## Experiment discipline

- Keep experiments small: often 1-3 days of wall-clock/compute.
- Most questions should die quickly -- that's fine, that's the point.
- Only expand a question when the result is surprising or ambiguous.
- AI (Claude/Codex agents) does implementation, literature search, plotting,
  and routine analysis. The human's highest-value role: choosing worthwhile
  questions, designing experiments, noticing anomalies, deciding what results
  actually mean.
- Every experiment gets a `config.yaml` with pinned commit hashes and
  immutable dataset/benchmark SHA-256 hashes (see `docs/reproducibility.md`,
  `docs/experiment-guide.md`, `docs/finetuning-playbook.md`).
- Findings worth keeping eventually get written up as a paper/report, not
  just left in scattered result directories.
