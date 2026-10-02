"""Offline regression checks using the cached pinned tokenizer; no Torch/model."""
import json
import unittest
from transformers import AutoTokenizer
from prepare_training import HERE, MODEL, REVISION, encode_final
from train_reviewed import collate_explicit

class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,local_files_only=True)
        cls.rows=[]
        for split in ('train','validation'):
            cls.rows.extend(json.loads(s) for s in (HERE/'reviewed-v2'/f'{split}-reviewed.jsonl').read_text(encoding='utf-8').splitlines())

    def test_all_rows_roundtrip_and_termination(self):
        for row in self.rows:
            item,prompt,target=encode_final(self.tokenizer,row)
            self.assertTrue(all(x==-100 for x in item['labels'][:prompt]))
            decoded=self.tokenizer.decode([x for x in item['labels'] if x!=-100],skip_special_tokens=False)
            self.assertEqual(decoded,row['desired_answer'].strip()+'<|im_end|>')

    def test_multi_turn_only_final(self):
        for id_ in ('me-053','me-054','me-059'):
            row=next(r for r in self.rows if r['id']==id_)
            item,prompt,_=encode_final(self.tokenizer,row)
            self.assertGreater(prompt,0)
            self.assertEqual(item['labels'][:prompt],[-100]*prompt)

    def test_padding_never_supervised(self):
        features=[encode_final(self.tokenizer,r)[0] for r in self.rows[:2]]
        batch=collate_explicit(features,self.tokenizer.pad_token_id)
        for i,f in enumerate(features):
            self.assertEqual(batch['labels'][i][:len(f['labels'])],f['labels'])
            self.assertTrue(all(x==-100 for x in batch['labels'][i][len(f['labels']):]))

    def test_no_validation_training_rows(self):
        train=[r for r in self.rows if r['split']=='train']
        val=[r for r in self.rows if r['split']=='validation']
        self.assertEqual(len(train),80)
        self.assertEqual(len(val),20)
        self.assertFalse({r['id'] for r in train}&{r['id'] for r in val})
        self.assertTrue(all(r['evaluation_only'] for r in val))

if __name__=='__main__':
    unittest.main()
