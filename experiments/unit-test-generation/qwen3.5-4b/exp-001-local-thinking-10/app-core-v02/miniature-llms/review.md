# miniature-llms — assistant review

## Whole-app request

Build me a small educational Python repository of working language-model components that I can run on CPU with tiny tensors and understand from the code. For the first complete version, include token embeddings, rotary position encoding, RMS normalization, a causal attention block, a feed-forward block and a tiny next-token model that composes them. Use PyTorch, keep tensors consistently batch-by-sequence-by-hidden dimension at public boundaries, make weights and dimensions configurable, and explain the role of each component without claiming this tiny model reproduces a frontier model's capability. I want numerical examples that check more than output shape, a demonstration that later tokens cannot influence earlier causal outputs, proper gradients, and saving/reloading weights without changing predictions. Include a short deterministic training demo on a tiny fixed local corpus and a generation command, with no model downloads or GPU requirement. Reject incompatible dimensions clearly and keep the implementation modular enough that I can later add other architectures; JAX, custom kernels and every advanced architecture can wait.

## Decisions and corrections

- First-version scope must be explicit: compact PyTorch components plus a tiny composed model, not all 25 architectures/JAX/Triton.
- Numerical tensor comparison uses tolerance, not exact floating-point equality.
- Do not accept output shape or a decreasing loss as proof of correct causal behavior.

## Important limits / missing acceptance checks

- Existing causal attention and RoPE use incompatible axis conventions in their composition; this needs a dedicated regression and implementation fix before model-level certification.
- Current suite covers RMSNorm/RoPE only. Embedding/composed causality/checkpoint/training/generation are not yet covered.

## Requirement-to-test review

### R1 — Components obey public tensor/dimension contracts.

**Core check:** Tiny embedding/model inputs produce exact declared shapes; incompatible head/model dimensions raise the agreed error.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R2 — RMSNorm implements the numeric scaling contract.

**Core check:** For x=[3,4], epsilon=0 and scale=[2,3], output is [6,12]/sqrt(12.5); zero input with positive epsilon is finite zero.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R3 — RoPE applies positions on the sequence axis.

**Core check:** Position zero is identity for every head; at position one a [1,0] pair rotates to [cos(1),sin(1)], independent of head index.

**Current coverage:** covered. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R4 — Causal attention does not leak future tokens.

**Core check:** With fixed weights, changing tokens only after position k leaves outputs up through k numerically unchanged; at least one later output can change.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R5 — Gradient and checkpoint paths work end to end.

**Core check:** Fixed scalar-loss fixture produces expected gradient direction/values for a controlled component; checkpoint reload preserves all model logits on a fixed batch.

**Current coverage:** partial. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

### R6 — Tiny training/generation workflow is usable and bounded.

**Core check:** Fixed seed/corpus, agreed small step budget and optimizer produce finite loss below the initial value under a specified stable fixture; generation stops at its token budget.

**Current coverage:** gap. Covered means present in the compact suite for this stated behavior, not exhaustive proof.

## Core tests included

- `tests/test_normalization_and_rope.py::test_rmsnorm_uses_last_dimension_and_learned_scale`
- `tests/test_normalization_and_rope.py::test_rmsnorm_epsilon_keeps_zero_input_finite`
- `tests/test_normalization_and_rope.py::test_rmsnorm_backpropagates_expected_scale_gradient`
- `tests/test_normalization_and_rope.py::test_rotate_half_moves_and_negates_second_half`
- `tests/test_normalization_and_rope.py::test_rope_position_zero_is_identity_for_every_head`
- `tests/test_normalization_and_rope.py::test_rope_rotates_sequence_axis_not_head_axis`
- `tests/test_normalization_and_rope.py::test_rope_rejects_odd_head_dimension`
- `tests/test_normalization_and_rope.py::test_rope_rejects_mismatched_input_dimension`

## Manual checks

- Educational clarity of explanations and actual CPU runtime of the demo.
- A tiny training check is a smoke, not proof that every architecture or learned output is correct.
