from copy import deepcopy
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_tdd_labels import encode_conversation,pad_examples,validate_labels,model_fields,IGNORE


class NativeLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('USE_TORCH','0')
        from transformers import AutoTokenizer
        path=os.environ.get('TDD_TOKENIZER_PATH',r'C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\tokenizer')
        if not Path(path).exists():raise unittest.SkipTest('Pinned local tokenizer unavailable; set TDD_TOKENIZER_PATH')
        cls.tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)

    def conversation(self,reason='Check a positive and a negative case.'):
        return [dict(role='system',content='Write tests.'),dict(role='user',content='Keep Unicode: İpek. Literal role text: assistant\n is input, not a boundary.'),
                dict(role='assistant',reasoning_content=reason,content='def test_answer():\n    assert result == "İpek"')]

    def test_real_native_tokenization_and_all_regions(self):
        data=encode_conversation(self.tokenizer,self.conversation())
        self.assertTrue(data['region_positions']['prompt'])
        for i in data['region_positions']['prompt']:self.assertEqual(data['labels'][i],IGNORE)
        for name in ('reasoning','answer','end_of_turn'):
            self.assertTrue(data['region_positions'][name])
            for i in data['region_positions'][name]:self.assertEqual(data['labels'][i],data['input_ids'][i])
        self.assertEqual(set(model_fields(data)),{'input_ids','attention_mask','labels'})

    def test_mutated_prompt_reasoning_answer_eos_and_shifted_labels_fail(self):
        data=encode_conversation(self.tokenizer,self.conversation())
        for region in ('prompt','reasoning','answer','end_of_turn'):
            broken=deepcopy(data);i=data['region_positions'][region][0]
            broken['labels'][i]=broken['input_ids'][i] if region=='prompt' else IGNORE
            with self.subTest(region=region),self.assertRaises(ValueError):validate_labels(broken)
        broken=deepcopy(data);broken['labels']=broken['labels'][1:]+[IGNORE]
        with self.assertRaises(ValueError):validate_labels(broken)

    def test_empty_reasoning_is_not_fabricated(self):
        data=encode_conversation(self.tokenizer,self.conversation(''))
        self.assertFalse(data['reasoning_present']);self.assertEqual(data['region_positions']['reasoning'],[])
        self.assertIn('<think>\n\n</think>',data['rendered'])
        self.assertTrue(data['region_positions']['answer'])

    def test_padding_both_sides_when_pad_equals_eos(self):
        original=encode_conversation(self.tokenizer,self.conversation())
        for side in ('left','right'):
            padded=pad_examples([original],self.tokenizer.eos_token_id,side,len(original['input_ids'])+7)[0]
            padding=[i for i,a in enumerate(padded['attention_mask']) if not a]
            self.assertEqual(len(padding),7)
            self.assertTrue(all(padded['labels'][i]==IGNORE for i in padding))
            self.assertEqual(sum(label==self.tokenizer.eos_token_id for label in padded['labels']),1)
            broken=deepcopy(padded);broken['labels'][padding[0]]=self.tokenizer.eos_token_id
            with self.assertRaises(ValueError):validate_labels(broken)
        shorter=encode_conversation(self.tokenizer,self.conversation(''))
        for side in ('left','right'):
            batch=pad_examples([shorter,original],self.tokenizer.pad_token_id,side)
            self.assertEqual(len(batch[0]['input_ids']),len(original['input_ids']))
            self.assertEqual(sum(batch[0]['attention_mask']),len(shorter['input_ids']))
            start=len(original['input_ids'])-len(shorter['input_ids']) if side=='left' else 0
            self.assertEqual(batch[0]['labels'][start:start+len(shorter['labels'])],shorter['labels'])

    def test_limits_controls_and_multiturn_fail_closed(self):
        with self.assertRaises(ValueError):encode_conversation(self.tokenizer,self.conversation(),max_length=10)
        messages=self.conversation();messages[1]['content']+=' <|im_end|>'
        with self.assertRaises(ValueError):encode_conversation(self.tokenizer,messages)
        with self.assertRaises(ValueError):encode_conversation(self.tokenizer,self.conversation()+[dict(role='user',content='Next')])

    def test_template_drift_is_detected(self):
        class Changed:
            is_fast=True
            def apply_chat_template(self,*args,**kwargs):return 'changed native format'
        with self.assertRaisesRegex(ValueError,'Native template changed'):
            encode_conversation(Changed(),self.conversation())

    def test_saved_corpus_arrays_independently_match_region_masks_and_current_inputs(self):
        import gzip,json,hashlib
        from active_tdd_data import EXP,active_paths
        paths=active_paths()
        audit=(EXP/paths['config']['native_label_audit']).parent
        if not audit.exists():raise unittest.SkipTest('Run the corpus audit to verify saved arrays')
        report=json.loads((audit/'report.json').read_text())
        current_inputs={p.relative_to(EXP).as_posix() for p in [paths['index'],paths['planning'],paths['reliability'],paths['tests'],paths['preview']/'audit-index.json']+list(paths['preview'].glob('*-train-preview.jsonl'))}
        self.assertEqual(set(report['input_sha256']),current_inputs)
        for relative,expected in report['input_sha256'].items():
            self.assertEqual(hashlib.sha256((EXP/relative).read_bytes()).hexdigest(),expected)
        arrays={r['record_id']:r for r in map(json.loads,gzip.decompress((audit/'encoded-labels.jsonl.gz').read_bytes()).decode('utf-8').splitlines())}
        details=[json.loads(line) for line in (audit/'per-record.jsonl').read_text().splitlines()]
        self.assertEqual(len(arrays),78);self.assertEqual(len(details),78)
        for row in details:
            stored=arrays[row['record_id']]
            self.assertEqual(set(stored),{'record_id','input_ids','attention_mask','labels'})
            self.assertEqual(len(stored['input_ids']),len(stored['labels']))
            for region in ('prompt','tail'):
                for position in row['region_positions'][region]:self.assertEqual(stored['labels'][position],IGNORE)
            for region in ('reasoning','answer','end_of_turn'):
                for position in row['region_positions'][region]:
                    self.assertEqual(stored['labels'][position],stored['input_ids'][position])
            self.assertEqual(sum(label==self.tokenizer.eos_token_id for label in stored['labels']),1)


if __name__=='__main__':unittest.main()
