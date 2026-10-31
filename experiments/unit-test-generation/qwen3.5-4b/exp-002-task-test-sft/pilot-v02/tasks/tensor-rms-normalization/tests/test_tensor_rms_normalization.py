import torch
from _7_RMSNorm.pytorch import RMSNorm


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
