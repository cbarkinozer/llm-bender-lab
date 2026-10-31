'Acceptance checks for observable application behavior.'
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
