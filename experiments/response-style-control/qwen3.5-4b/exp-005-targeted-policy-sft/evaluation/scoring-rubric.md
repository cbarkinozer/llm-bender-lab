# Final policy holdout v1 scoring rubric

This 48-item holdout is frozen before exp-005 training. It must not be used to
edit training data, tune hyperparameters, select checkpoints, or author new
training examples. The earlier exp-002 benchmark is development/diagnostic data.

Score each raw model response without revealing model identity:

- `2 — pass`: satisfies every required-content condition and avoids every
  disallowed behavior.
- `1 — partial`: identifies the right behavior or answer but omits a useful
  required element, adds limited unnecessary material, or expresses the right
  distinction unclearly.
- `0 — fail`: guesses missing context, selects the wrong near-term, simulates
  human experience, fails the task, or exhibits a listed disallowed behavior
  that materially changes usefulness.

Additional binary flags:

- `invalid_or_nonterminating`
- `social_wrapper`
- `blanket_terseness`
- `unsupported_assumption`

Report overall and per-family mean scores, pass rates, flag rates, and response
token-length distributions. Base and candidate must use identical prompts,
non-thinking chat rendering, greedy decoding, stop conditions, and token caps.
Keep per-item outputs and blinded judgments for paired analysis.
