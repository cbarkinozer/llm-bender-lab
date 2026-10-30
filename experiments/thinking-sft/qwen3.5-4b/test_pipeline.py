"""Offline checks of data separation, real native labels, arithmetic, and EOS padding."""
import copy
import csv
from fractions import Fraction
import unittest
import tempfile
import json
from pathlib import Path

from pipeline import DATA, MODEL, REVISION, validate, read_rows, encode_training
from train import LabelCollator
from evaluate import split_reasoning
from review import summarize


class DataChecks(unittest.TestCase):
    def setUp(self):
        with (DATA / 'authored-cases.tsv').open(newline='') as f:
            self.cases = list(csv.DictReader(f, delimiter='\t'))

    def test_split_and_counts(self):
        counts, flags = validate(self.cases)
        self.assertEqual(sum(n for (s, _), n in counts.items() if s == 'train'), 80)
        self.assertEqual(sum(n for (s, _), n in counts.items() if s == 'test'), 20)
        self.assertEqual(flags, [])
        prompts = read_rows(DATA / 'test-prompts.jsonl')
        self.assertTrue(all([m['role'] for m in r['messages']] == ['system', 'user'] for r in prompts))
        self.assertTrue(all('reference_answer' not in r and 'worked_solution' not in r for r in prompts))

    def test_cross_split_duplicate_is_rejected(self):
        changed = copy.deepcopy(self.cases)
        train = next(r for r in changed if r['split'] == 'train')
        test = next(r for r in changed if r['split'] == 'test')
        test['prompt'] = train['prompt']
        with self.assertRaisesRegex(ValueError, 'Duplicate prompt'):
            validate(changed)

    def test_numerical_reference_checks(self):
        answers = {r['group_id']: r['answer'] for r in self.cases}
        # Recompute numerical outcomes rather than copying authored solution strings.
        calculated = {
            'unit-price-shipping': [str(4*135), str((4*120+80)-4*135)],
            'sequential-discounts': [str(int(1000*Fraction(8,10)*Fraction(9,10)))],
            'inventory-net': [str(86-12-9+20)],
            'pack-rounding': [str((65+7)//8)],
            'dependency-parallel': [str(2+max(3,1)+2)],
            'capacity-shared': [str(45+70+5)],
            'budget-tax': [str(int(5200*Fraction(12,10)-6000))],
            'weighted-average': [str((30*2+60)//3)],
            'minimum-order': [str(max(42,50)*18), str(50-42)],
            'subscription-break-even': [str(30*9-(100+30*5)), str(100+30*5)],
            'refund-partial': [str(int(900//3*Fraction(9,10)))],
            'space-reserve': [str(20-(120-35-70))],
            'speed-change': [str(100//50+120//40)],
            'worker-independent': [str(((3+1)//2)*6)],
            'route-selection': [str(40+25-55)],
            'refund-reorder-net': [str(650+70-480)],
            'uncertainty-reduction': [str(12+8)],
        }
        for group, values in calculated.items():
            for value in values:
                self.assertIn(value, answers[group], group)
        def clock(minutes):
            return f'{minutes//60:02d}.{minutes%60:02d}'
        times = {
            'batch-throughput': 9*60+720//240*60+30,
            'break-time': 9*60+30+3*60+30,
            'travel-buffer': 14*60-15-50-10,
            'printing-finishing-overlap': 8*60+250*60//(40+60)+45,
            'conference-resource': 13*60+50+40+10,
        }
        for group, minutes in times.items():
            self.assertIn(clock(minutes), answers[group], group)
        self.assertIn('1.290', answers['procurement-bundles'])
        self.assertEqual(((60+24)//25)*400+90, 1290)
        self.assertEqual(60*22-1290, 30)
        self.assertEqual(11*60+30+50+40, 13*60)
        self.assertIn(str((min(12,13)-max(10,11))*60), answers['meeting-intersection'])
        self.assertIn(str(10+4), answers['deadline-inclusive-count'])

    def test_reasoning_parser_retains_incomplete_attempt(self):
        self.assertEqual(split_reasoning('Hesap tamam değil'), ('Hesap tamam değil', ''))
        self.assertEqual(split_reasoning('Kontrol edildi.\n</think>\nEvet.<|im_end|>'),
                         ('Kontrol edildi.', 'Evet.'))

    def test_padding_does_not_mask_real_eos(self):
        result = LabelCollator(9)([
            dict(input_ids=[1, 9], attention_mask=[1, 1], labels=[-100, 9]),
            dict(input_ids=[1, 2, 9], attention_mask=[1, 1, 1], labels=[-100, 2, 9])])
        self.assertEqual(result['labels'].tolist(), [[-100, 9, -100], [-100, 2, 9]])
        self.assertEqual(result['attention_mask'].tolist()[0], [1, 1, 0])

    def test_review_refuses_unrated_results(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            rows = [dict(id=str(i), A=dict(semantic_score=None), B=dict(semantic_score=1)) for i in range(20)]
            (folder/'ratings.json').write_text(json.dumps(rows))
            (folder/'mapping.json').write_text(json.dumps({str(i):dict(A='base', B='adapter') for i in range(20)}))
            with self.assertRaisesRegex(ValueError, 'Unrated'):
                summarize(folder)
            self.assertFalse((folder/'summary.json').exists())


class NativeTemplateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoTokenizer
        cls.tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION,
                                                       local_files_only=True, trust_remote_code=False)

    def test_all_training_reasoning_and_answers_are_supervised(self):
        for row in read_rows(DATA / 'train.jsonl'):
            encoded, stats, suffix = encode_training(self.tokenizer, row, 1024)
            selected = [i for i in encoded['labels'] if i != -100]
            self.assertEqual(self.tokenizer.decode(selected, skip_special_tokens=False), suffix)
            self.assertGreater(stats['reasoning_tokens'], 0)
            self.assertGreater(stats['answer_tokens'], 0)
            self.assertEqual(suffix.count('<think>'), 1)
            self.assertEqual(suffix.count('</think>'), 1)

    def test_truncation_fails_instead_of_dropping_answer(self):
        row = read_rows(DATA / 'train.jsonl')[0]
        with self.assertRaisesRegex(ValueError, 'would truncate'):
            encode_training(self.tokenizer, row, 10)

    def test_small_hybrid_model_receives_lora_gradients(self):
        # Random tiny architecture checks the training path, not pretrained 4B quality.
        import torch
        from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
        from peft import LoraConfig, TaskType, get_peft_model
        torch.manual_seed(3407)
        config = Qwen3_5Config(text_config=dict(vocab_size=128, hidden_size=32,
            intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
            num_key_value_heads=1, head_dim=16, layer_types=['linear_attention', 'full_attention'],
            linear_num_key_heads=2, linear_num_value_heads=2, linear_key_head_dim=16,
            linear_value_head_dim=16, max_position_embeddings=128,
            rope_parameters={'rope_type':'default', 'rope_theta':10000., 'partial_rotary_factor':1.0}),
            vision_config=dict(depth=1, hidden_size=32, num_heads=2, intermediate_size=64,
                               out_hidden_size=32, num_position_embeddings=16))
        model = Qwen3_5ForConditionalGeneration(config)
        names = [n for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)
                 and 'language_model' in n and n.rsplit('.',1)[-1] in
                 ['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']]
        model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM,
            r=2, lora_alpha=2, target_modules=names))
        batch = LabelCollator(9)([dict(input_ids=[1,2,3,9], attention_mask=[1]*4,
                                     labels=[-100,-100,3,9])])
        loss = model(**batch, use_cache=False).loss
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum().item() > 0
                            for n, p in model.named_parameters() if 'lora_' in n))


if __name__ == '__main__':
    unittest.main()
