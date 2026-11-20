import json,hashlib
from pathlib import Path
from transformers import AutoTokenizer
root=Path('/workspace/reflex-wsp');models=json.loads((root/'models.json').read_text())
names=['parent','wsp','original_training_base'];ts={k:AutoTokenizer.from_pretrained(models[k]) for k in names}
reference=ts['parent'];report={}
for k,t in ts.items():
    cfg=json.loads((Path(models[k])/'config.json').read_text())
    base=json.loads((Path(models['parent'])/'config.json').read_text())
    changes={key:{'parent':base.get(key),'arm':cfg.get(key)} for key in sorted(base.keys()|cfg.keys()) if base.get(key)!=cfg.get(key)}
    report[k]={'vocab_equal_parent':t.get_vocab()==reference.get_vocab(),'special_tokens_equal_parent':t.special_tokens_map==reference.special_tokens_map,'chat_template_equal_parent':t.chat_template==reference.chat_template,'config_differences':changes}
(root/'tokenizer-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)