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
