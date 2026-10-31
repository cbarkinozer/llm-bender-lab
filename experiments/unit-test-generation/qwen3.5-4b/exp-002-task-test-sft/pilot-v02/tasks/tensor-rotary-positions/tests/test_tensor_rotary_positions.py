import pytest
import torch
from _4_RoPE.pytorch import RoPE, rotate_half


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
