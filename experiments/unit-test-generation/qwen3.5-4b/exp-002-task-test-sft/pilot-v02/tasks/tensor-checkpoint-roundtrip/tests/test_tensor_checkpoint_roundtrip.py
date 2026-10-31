import torch


def model():
    from tiny_model import TinyModel
    torch.manual_seed(7)
    return TinyModel(vocab_size=8, hidden_dim=8, num_heads=2, max_length=16)


def test_checkpoint_roundtrip_preserves_all_logits(tmp_path):
    from tiny_model import TinyModel
    net = model().eval()
    tokens = torch.tensor([[1,2,3]])
    expected = net(tokens).detach()
    path = tmp_path/'weights.pt'
    net.save(path)
    restored = TinyModel.load(path).eval()
    torch.testing.assert_close(restored(tokens), expected, rtol=0,atol=0)
