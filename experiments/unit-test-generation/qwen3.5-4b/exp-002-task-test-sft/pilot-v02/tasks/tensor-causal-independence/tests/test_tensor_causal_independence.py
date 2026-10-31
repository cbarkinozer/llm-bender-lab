import torch


def model():
    from tiny_model import TinyModel
    torch.manual_seed(7)
    return TinyModel(vocab_size=8, hidden_dim=8, num_heads=2, max_length=16)


def test_causal_outputs_cannot_observe_future_tokens():
    net = model().eval()
    with torch.no_grad():
        original = net(torch.tensor([[1,2,3,4]]))
        changed = net(torch.tensor([[1,2,6,7]]))
    torch.testing.assert_close(original[:,:2], changed[:,:2], rtol=1e-5,atol=1e-6)
    assert not torch.allclose(original[:,2:],changed[:,2:])
