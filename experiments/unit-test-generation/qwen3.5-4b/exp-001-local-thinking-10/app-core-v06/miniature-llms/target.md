## Decisions and unresolved questions

Proposed decisions:

- Use configurable tiny PyTorch components and a composed CPU model.
- Use tolerance-based numerical tensor checks and exact same-runtime checkpoint comparisons.
- Check causal behavior and actual predicted generation tokens independently of tensor shape or loss reduction.

Unresolved/nonessential choices:
- Tokenizer for a larger text corpus and real-language generation quality are out of this fixed token-fixture contract.

## Proposed interface agreement

Proposed components plus new public `tiny_model`:
- `_7_RMSNorm.pytorch.RMSNorm(dimension,epsilon=...)` is a PyTorch layer with trainable `.weight`; normalize last dimension by sqrt(mean(x²)+epsilon), then multiply weight. Positive epsilon maps zero input to finite zeros; gradients must match formula.
- `_4_RoPE.pytorch.rotate_half(x)` concatenates negative second half and first half along last dimension. `RoPE(head_dimension,max_sequence_length,base=10000)` takes [batch,sequence,head,head_dimension], rotates sequence positions, position0 identity. Odd dimension -> ValueError mentioning "head_dimension must be even"; wrong forward dimension -> ValueError "Expected head dimension <n>, got <n>".
- `tiny_model.TinyModel(vocab_size,hidden_dim,num_heads,max_length)` takes integer tokens [batch,sequence], returns logits [batch,sequence,vocab]. Contains embedding, RoPE, RMSNorm, causal attention and feed-forward path; hidden_dim divisible by num_heads with even per-head dimension, otherwise ValueError. CPU tensors, configurable tiny sizes. Future token changes cannot affect earlier logits, yet later logits must be input-sensitive. All trainable parameters have finite gradients under the fixture loss and at least one nonzero gradient.
- `.save(path)` / `TinyModel.load(path)` preserve config and all weights; eval-mode logits exactly preserved on same CPU fixture. Files contain only local tensors/config, no downloaded state.
- `train_demo(tokens,seed=...,steps=...,learning_rate=...)` -> `{model,losses}`. Demo model config (vocab8,hidden8,heads2,maxlen16), AdamW optimizer and provided repeating corpus, deterministic CPU seed; 30 steps at .03 produce finite improving loss.
- `generate(model,prompt_ids,max_new_tokens=...)` -> complete token list, greedy decoding with exact requested additional length (no EOS in this fixture vocabulary), retaining prompt; reject negative budget.
Dependencies: Python, pytest, PyTorch; no GPU/network/model downloads. Educational prose and actual CLI wiring remain manual checks.

Public imports:
- `_4_RoPE.pytorch.RoPE`
- `_4_RoPE.pytorch.rotate_half`
- `_7_RMSNorm.pytorch.RMSNorm`
- `tiny_model.TinyModel`
- `tiny_model.generate`
- `tiny_model.train_demo`

## Requirement-to-test map

R1: Components obey public tensor/dimension contracts.
- `tests/test_normalization_and_rope.py::test_rope_rejects_odd_head_dimension`
- `tests/test_normalization_and_rope.py::test_rope_rejects_mismatched_input_dimension`
- `tests/test_workflow.py::test_composed_model_shapes_gradients_and_invalid_dimensions`

R2: RMSNorm implements the numeric scaling contract.
- `tests/test_normalization_and_rope.py::test_rmsnorm_uses_last_dimension_and_learned_scale`
- `tests/test_normalization_and_rope.py::test_rmsnorm_epsilon_keeps_zero_input_finite`
- `tests/test_normalization_and_rope.py::test_rmsnorm_backpropagates_expected_scale_gradient`

R3: RoPE applies positions on the sequence axis.
- `tests/test_normalization_and_rope.py::test_rotate_half_moves_and_negates_second_half`
- `tests/test_normalization_and_rope.py::test_rope_position_zero_is_identity_for_every_head`
- `tests/test_normalization_and_rope.py::test_rope_rotates_sequence_axis_not_head_axis`
- `tests/test_normalization_and_rope.py::test_rope_rejects_odd_head_dimension`
- `tests/test_normalization_and_rope.py::test_rope_rejects_mismatched_input_dimension`

R4: Causal attention does not leak future tokens.
- `tests/test_workflow.py::test_causal_outputs_cannot_observe_future_tokens`

R5: Gradient and checkpoint paths work end to end.
- `tests/test_normalization_and_rope.py::test_rmsnorm_backpropagates_expected_scale_gradient`
- `tests/test_workflow.py::test_composed_model_shapes_gradients_and_invalid_dimensions`
- `tests/test_workflow.py::test_checkpoint_roundtrip_preserves_all_logits`

R6: Tiny training/generation workflow is usable and bounded.
- `tests/test_workflow.py::test_deterministic_cpu_training_and_bounded_generation`
- `tests/test_workflow.py::test_greedy_generation_follows_unique_logit_maxima`
- `tests/test_workflow.py::test_negative_generation_budget_is_rejected`

R7: Usable delivery, documented commands and the declared live/manual integration checks.

Manual/live: M1, M2

## Complete test files

File: tests/test_normalization_and_rope.py
```python
'Acceptance checks for observable application behavior.'
import sys
from pathlib import Path
import pytest
import torch

from _7_RMSNorm.pytorch import RMSNorm
from _4_RoPE.pytorch import RoPE, rotate_half


def test_rmsnorm_uses_last_dimension_and_learned_scale():
    layer = RMSNorm(2, epsilon=0.)
    with torch.no_grad():
        layer.weight.copy_(torch.tensor([2., 3.]))
    x = torch.tensor([[[3., 4.], [0., 5.]]])
    expected = torch.tensor([[[6. / (12.5 ** .5), 12. / (12.5 ** .5)], [0., 15. / (12.5 ** .5)]]])
    torch.testing.assert_close(layer(x), expected)


def test_rmsnorm_epsilon_keeps_zero_input_finite():
    layer = RMSNorm(3)
    torch.testing.assert_close(layer(torch.zeros(2, 3)), torch.zeros(2, 3))


def test_rmsnorm_backpropagates_expected_scale_gradient():
    layer = RMSNorm(2, epsilon=0.)
    x = torch.tensor([[3., 4.]])
    layer(x).sum().backward()
    torch.testing.assert_close(layer.weight.grad, torch.tensor([3., 4.]) / (12.5 ** .5))


def test_rotate_half_moves_and_negates_second_half():
    x = torch.tensor([[[[1., 2., 3., 4.]]]])
    torch.testing.assert_close(rotate_half(x), torch.tensor([[[[-3., -4., 1., 2.]]]]))


def test_rope_position_zero_is_identity_for_every_head():
    x = torch.tensor([[[[1., 2., 3., 4.], [5., 6., 7., 8.]]]])
    torch.testing.assert_close(RoPE(4, 8)(x), x)


def test_rope_rotates_sequence_axis_not_head_axis():
    layer = RoPE(2, 4)
    x = torch.tensor([[[[1., 0.], [1., 0.]], [[1., 0.], [1., 0.]]]])
    expected = torch.tensor([[[[1., 0.], [1., 0.]], [[torch.cos(torch.tensor(1.)).item(), torch.sin(torch.tensor(1.)).item()], [torch.cos(torch.tensor(1.)).item(), torch.sin(torch.tensor(1.)).item()]]]])
    torch.testing.assert_close(layer(x), expected)


def test_rope_rejects_odd_head_dimension():
    with pytest.raises(ValueError, match='head_dimension must be even'):
        RoPE(3, 8)


def test_rope_rejects_mismatched_input_dimension():
    with pytest.raises(ValueError, match='Expected head dimension 4, got 2'):
        RoPE(4, 8)(torch.ones(1, 2, 1, 2))
```

File: tests/test_workflow.py
```python
'Acceptance checks for observable application behavior.'
import torch
import pytest


def model():
    from tiny_model import TinyModel
    torch.manual_seed(7)
    return TinyModel(vocab_size=8, hidden_dim=8, num_heads=2, max_length=16)


def test_composed_model_shapes_gradients_and_invalid_dimensions():
    from tiny_model import TinyModel
    net = model()
    out = net(torch.tensor([[1,2,3]]))
    assert out.shape == (1,3,8)
    out.square().sum().backward()
    grads = [p.grad for p in net.parameters() if p.requires_grad]
    assert all(g is not None and torch.isfinite(g).all() for g in grads)
    assert sum(g.abs().sum().item() for g in grads) > 0
    with pytest.raises(ValueError):
        TinyModel(vocab_size=8, hidden_dim=7, num_heads=2, max_length=16)


def test_causal_outputs_cannot_observe_future_tokens():
    net = model().eval()
    with torch.no_grad():
        original = net(torch.tensor([[1,2,3,4]]))
        changed = net(torch.tensor([[1,2,6,7]]))
    torch.testing.assert_close(original[:,:2], changed[:,:2], rtol=1e-5,atol=1e-6)
    assert not torch.allclose(original[:,2:],changed[:,2:])


def test_checkpoint_roundtrip_preserves_all_logits(tmp_path):
    from tiny_model import TinyModel
    net = model().eval()
    tokens = torch.tensor([[1,2,3]])
    expected = net(tokens).detach()
    path = tmp_path/'weights.pt'
    net.save(path)
    restored = TinyModel.load(path).eval()
    torch.testing.assert_close(restored(tokens), expected, rtol=0,atol=0)


def test_deterministic_cpu_training_and_bounded_generation():
    from tiny_model import train_demo, generate
    tokens = torch.tensor([[1,2,1,2,1]])
    first = train_demo(tokens, seed=7, steps=30, learning_rate=.03)
    second = train_demo(tokens, seed=7, steps=30, learning_rate=.03)
    assert first['losses'] == second['losses']
    assert all(torch.isfinite(torch.tensor(first['losses'])))
    assert first['losses'][-1] < first['losses'][0]
    output = generate(first['model'], [1], max_new_tokens=3)
    assert output[:1] == [1]
    assert len(output) == 4
    assert all(0 <= token < 8 for token in output)


@pytest.mark.parametrize('budget,expected', [(0,[1]),(3,[1,2,3,4])])
def test_greedy_generation_follows_unique_logit_maxima(budget, expected):
    from tiny_model import generate
    class SuccessorModel(torch.nn.Module):
        def forward(self, tokens):
            # Every position predicts (its current token + 1) mod 8 uniquely.
            logits = torch.full((*tokens.shape, 8), -10.0)
            return logits.scatter(-1, ((tokens+1)%8).unsqueeze(-1), 10.0)
    assert generate(SuccessorModel(), [1], max_new_tokens=budget) == expected


def test_negative_generation_budget_is_rejected():
    from tiny_model import generate
    with pytest.raises(ValueError):
        generate(model(), [1], max_new_tokens=-1)
```

## Manual checks

M1: Check educational explanations and run the documented CPU training/generation commands.
M2: Verify commands invoke the composed model and require no weight downloads or GPU.
