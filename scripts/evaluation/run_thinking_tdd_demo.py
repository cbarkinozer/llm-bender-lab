"""Fixed-budget local baseline. Saves every SSE event; never executes generated code."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = EXP / 'requirements.jsonl'
    tasks = [json.loads(x) for x in source.read_text().splitlines() if x]
    settings = dict(model='qwen3.5-4b-q4-k-m', temperature=0.6, top_p=0.95,
                    top_k=20, repeat_penalty=1.05, seed=42, max_tokens=8192,
                    chat_template_kwargs={'enable_thinking': True}, stream=True,
                    stream_options={'include_usage': True})
    system = 'You generate Python pytest tests from requirements. Follow the user\'s requested output format.'
    manifest = dict(created=datetime.now(timezone.utc).isoformat(), settings=settings,
                    backend='llama.cpp direct HTTP, GGUF Q4_K_M', context_tokens=16384,
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    task_ids=[t['id'] for t in tasks], system_prompt=system,
                    git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    note='One attempt per task; no repairs. Direct HTTP avoids agent tooling and preserves raw reasoning. 8192 shared thinking/answer cap, no adaptive retries.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'runner.py').write_bytes(Path(__file__).read_bytes())
    (out/'requirements.jsonl').write_bytes(source.read_bytes())
    (out/'working-tree.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    with urlopen('http://127.0.0.1:18080/props',timeout=5) as r:
        props=json.load(r)
    (out/'server-props.json').write_text(json.dumps(props,indent=2))
    assert props['default_generation_settings']['n_ctx']==16384
    summaries=[]
    for task in tasks:
        item=out/task['id']; item.mkdir()
        prompt=(f"Write pytest tests for the following public API.\nModule: {task['module']}\n"
                f"Function: {task['signature']}\nRequirements:\n{task['requirements']}\n"
                f"Output: {task['model_output']}\nImport the function from solution. Do not implement it. "
                'Use only pytest and the Python standard library. Return one Python code block containing the complete test module.')
        payload={**settings,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}]}
        (item/'request.json').write_text(json.dumps(payload,indent=2))
        content=''; thinking=''; finish=None; usage={}; error=None; start=time.monotonic()
        print('START',task['id'],flush=True)
        try:
            request=Request('http://127.0.0.1:18080/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=120) as response, (item/'events.jsonl').open('w') as events:
                for line in response:
                    if not line.startswith(b'data: '): continue
                    data=line[6:].strip()
                    if data==b'[DONE]': break
                    event=json.loads(data); events.write(json.dumps(event)+'\n'); events.flush()
                    usage=event.get('usage') or usage
                    for choice in event.get('choices',[]):
                        delta=choice.get('delta',{})
                        content+=delta.get('content') or ''
                        thinking+=delta.get('reasoning_content') or delta.get('reasoning') or ''
                        finish=choice.get('finish_reason') or finish
        except Exception as exc:
            error=repr(exc)
        (item/'answer.md').write_text(content)
        (item/'thinking.txt').write_text(thinking)
        blocks=re.findall(r'```(?:python|py)?\s*\n(.*?)```',content,re.S)
        code=blocks[0] if len(blocks)==1 else content.strip()
        syntax_error=None
        try: ast.parse(code)
        except SyntaxError as exc: syntax_error=str(exc)
        (item/'generated_tests.py').write_text(code+'\n')
        summary=dict(task_id=task['id'],seconds=round(time.monotonic()-start,2),finish_reason=finish,
                     usage=usage,error=error,syntax_error=syntax_error,thinking_chars=len(thinking),answer_chars=len(content),
                     truncated=finish=='length',code_blocks=len(blocks))
        (item/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        summaries.append(summary)
        (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
        print('DONE',json.dumps(summary),flush=True)
    print('COMPLETE',out,flush=True)

if __name__=='__main__': main()
