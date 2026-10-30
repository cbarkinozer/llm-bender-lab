"""Inventory repository-owned test sources with the local Qwen tokenizer; no code execution."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tokenizers import Tokenizer

REPOS=['GitHub-insignia','ghost-box','slm_test_generation','llm-bender-lab','ReflexModels','codelang-detect','repo-context','cryptocurrency-analyser','miniature-llms']
ROOT=Path('/Users/cbarkinozer/Documents/GitHub')
TOKENIZER=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts/occam-gguf-20261026/base/tokenizer.json')

def main():
    tokenizer=Tokenizer.from_file(str(TOKENIZER));rows=[]
    for name in REPOS:
        repo=ROOT/name
        files=subprocess.check_output(['rg','--files','--hidden','-g','!.git','-g','!uv.lock'],cwd=repo,text=True).splitlines()
        records=[]
        for relative in files:
            path=Path(relative)
            if path.suffix!='.py' or not (path.name.startswith('test_') or path.name.endswith('_test.py') or path.name=='conftest.py'):continue
            source=(repo/path).read_text(encoding='utf-8-sig'); tree=ast.parse(source)
            records.append(dict(path=relative,chars=len(source),tokens=len(tokenizer.encode(source,add_special_tokens=False).ids),sha256=sha256(source.encode()).hexdigest(),test_functions=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test') for n in ast.walk(tree)),assert_statements=sum(isinstance(n,ast.Assert) for n in ast.walk(tree)),unittest_assert_calls=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(tree))))
        testfiles=[r for r in records if Path(r['path']).name!='conftest.py']
        rows.append(dict(repo=name,commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),test_files=len(testfiles),test_functions=sum(r['test_functions'] for r in testfiles),test_chars=sum(r['chars'] for r in testfiles),test_tokens=sum(r['tokens'] for r in testfiles),fixture_tokens=sum(r['tokens'] for r in records if Path(r['path']).name=='conftest.py'),max_file_tokens=max((r['tokens'] for r in testfiles),default=0),files=records))
    report=dict(tokenizer=str(TOKENIZER),tokenizer_sha256=sha256(TOKENIZER.read_bytes()).hexdigest(),notes=['Repository-owned sources discovered by rg; generated benchmark predictions and external tests are not dataset candidates.','Token totals exclude future requirement, reasoning, chat formatting and other fixture dependencies. Never equate these totals with full SFT sequence length.','Static test functions are not collected parameterized case counts. Assertion presence is not semantic correctness or measured coverage.','slm_test_generation frozen benchmark items and llm-bender evaluation contracts must remain excluded from training.'],repositories=rows)
    out=ROOT/'llm-bender-lab/experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/repo-source-audit.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    for r in rows:print(r['repo'],r['test_files'],r['test_functions'],r['test_chars'],r['test_tokens'],r['max_file_tokens'])

if __name__=='__main__':main()
