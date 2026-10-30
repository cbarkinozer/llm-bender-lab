# exp-000 — untouched Qwen3.5-4B thinking-on baseline

The primary baseline is CUDA BF16 Transformers inference on the pinned original
checkpoint, batch1, using the frozen experiment config. It has not run.
Candidate evaluation uses the same model/runtime/settings plus the final adapter.

Local Mac GGUF inference is a development diagnostic only: the existing Q4_K_M
artifact has a different representation, so its outputs must not be presented as
the matched BF16 baseline. `evaluate.py --backend http` permits development
prompts only. The four development probes never enter the 80 training examples
or the 20 held-out tests. Preserve their original failures without silent reruns.

Local diagnostic completed 2026-10-28: three of four attempts reached the 4096-token
limit without a final answer. The one naturally completed attempt answered its
scheduling question correctly. The first trace was predominantly English despite
the Turkish instruction. See [original diagnostic summary](local-dev-summary.json).
No prompts or sampling were changed in response; no incorrect-answer retries ran.
This is concrete development evidence of termination/language issues, not a
held-out accuracy measurement or evidence of any SFT improvement.

Raw local requests/responses, server properties and logs are retained outside Git
under `~/Documents/llm-bender-artifacts/occam2/dev-local-v1` and `dev-server.log`.
The dedicated development server was stopped after the run.

Use [RUN.md](../RUN.md). Test prompts are kept separate from scoring keys;
the inference runner never reads reference answers or worked test solutions.
