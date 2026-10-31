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
    for hidden in (7,6):
        with pytest.raises(ValueError):
            TinyModel(vocab_size=8, hidden_dim=hidden, num_heads=2, max_length=16)
