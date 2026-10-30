"""Fresh data fixtures test preprocessing, actual native labels and honest review."""
import copy
import json
import pytest
from transformers import AutoTokenizer
from pipeline import CATEGORIES, validate, encode_training
from train import LabelCollator
from evaluate import split_reasoning
from review import summarize


@pytest.fixture
def cases():
    return [dict(split=split, category=category, group_id=f'{split}-{category}-{index}', prompt=f'Unique {split} {category} scenario {index}', reasoning='Check the stated inputs.', answer='A valid result.') for split, count in [('train', 20), ('test', 5)] for category in CATEGORIES for index in range(count)]


@pytest.fixture(scope='module')
def tokenizer():
    import os
    return AutoTokenizer.from_pretrained(os.environ['TDD_TOKENIZER_PATH'], local_files_only=True, trust_remote_code=False)


@pytest.fixture
def training_row():
    return {'id': 'fresh', 'messages': [{'role': 'system', 'content': 'Follow the requirement.'}, {'role': 'user', 'content': 'Return the total for 2 and 3.'}, {'role': 'assistant', 'reasoning_content': 'Adding 2 and 3 gives 5.', 'content': '5'}]}


def test_preflight_accepts_expected_split_sizes(cases):
    counts, _ = validate(cases)
    assert sum(n for (split, _), n in counts.items() if split == 'train') == 80
    assert sum(n for (split, _), n in counts.items() if split == 'test') == 20


def test_cross_split_duplicate_is_rejected(cases):
    changed = copy.deepcopy(cases)
    changed[-1]['prompt'] = changed[0]['prompt']
    with pytest.raises(ValueError, match='Duplicate prompt'):
        validate(changed)


def test_empty_answer_is_rejected(cases):
    cases[0]['answer'] = ' '
    with pytest.raises(ValueError, match='Empty field'):
        validate(cases)


def test_actual_native_labels_supervise_reasoning_and_answer(tokenizer, training_row):
    encoded, _, suffix = encode_training(tokenizer, training_row, 2048)
    selected = [token for token in encoded['labels'] if token != -100]
    assert tokenizer.decode(selected, skip_special_tokens=False) == '<think>\nAdding 2 and 3 gives 5.\n</think>\n\n5<|im_end|>\n'
    assert suffix.endswith('5<|im_end|>\n')
    assert encoded['labels'][0] == -100


def test_truncation_fails_instead_of_discarding_target(tokenizer, training_row):
    with pytest.raises(ValueError, match='would truncate'):
        encode_training(tokenizer, training_row, 8)


def test_malformed_conversation_roles_are_rejected(tokenizer, training_row):
    training_row['messages'][-1]['role'] = 'user'
    with pytest.raises(ValueError, match='system/user/assistant'):
        encode_training(tokenizer, training_row, 2048)


def test_padding_preserves_real_eos_labels():
    result = LabelCollator(9)([dict(input_ids=[1, 9], attention_mask=[1, 1], labels=[-100, 9]), dict(input_ids=[1, 2, 9], attention_mask=[1, 1, 1], labels=[-100, 2, 9])])
    assert result['labels'].tolist() == [[-100, 9, -100], [-100, 2, 9]]
    assert result['attention_mask'].tolist() == [[1, 1, 0], [1, 1, 1]]


def test_incomplete_reasoning_is_not_fabricated_into_an_answer():
    assert split_reasoning('Still working') == ('Still working', '')
    assert split_reasoning('<think>Checked.\n</think>\n5<|im_end|>') == ('Checked.', '5')


def test_unrated_comparison_cannot_publish_summary(tmp_path):
    ratings = [dict(id=str(i), A=dict(semantic_score=None), B=dict(semantic_score=1)) for i in range(20)]
    (tmp_path / 'ratings.json').write_text(json.dumps(ratings))
    (tmp_path / 'mapping.json').write_text(json.dumps({str(i): dict(A='base', B='adapter') for i in range(20)}))
    with pytest.raises(ValueError, match='Unrated'):
        summarize(tmp_path)
    assert (tmp_path / 'summary.json').exists() is False
