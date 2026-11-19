"""CPU contract checks; synthetic subprocess outputs do not validate GPU/model quality."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import sys
import unittest
from unittest.mock import patch

import run_lfm3_stage_diagnostic as runner
sys.path.insert(0,str(runner.ROOT/'scripts/training'))
import lfm3_stage_pod as client
import fetch_lfm3_session as fetch

class StageDiagnosticContracts(unittest.TestCase):
    def test_freeze_and_upload_boundaries(self):
        m=runner.verify();self.assertEqual(m['outputs'],264)
        receipt=runner.read(runner.DATA/'bundle-receipt.json')
        archive=runner.OUT/'pod-input.tar.gz'
        self.assertEqual(runner.sha(archive),receipt['sha256'])
        with tarfile.open(archive) as t:
            names={p.name for p in t.getmembers() if p.isfile()}
            self.assertEqual(names,set(m['files'])|{(runner.DATA/'freeze.json').relative_to(runner.ROOT).as_posix()})
            self.assertFalse(any('references-local-only' in n or 'arithmetic-reference-audit' in n for n in names))
            self.assertEqual([n for n in names if n.endswith('.safetensors')],
                ['experiments/turkish-capability/lfm3-1.7b/exp-011-bilingual-sft640/results-local/sft/checkpoint-69/adapter_model.safetensors'])
        audit=runner.read(runner.DATA/'arithmetic-reference-audit.json')
        missing=[(r['group_id'],d['missing_markers']) for r in audit for d in r['directions'].values() if d['missing_markers']]
        self.assertEqual(missing,[('bp01-g104',['18000'])]*4)

    def test_job_counts_resume_and_mode_guard(self):
        jobs=[]
        def fake_subprocess(cmd,**kwargs):
            args=list(map(str,cmd));dest=Path(args[args.index('--output-dir')+1]);packet=Path(args[args.index('--packet-path')+1])
            prompts=runner.rows(packet);thinking='--enable-thinking' in args
            dest.mkdir(parents=True)
            runner.dump(dest/'manifest.json',dict(status='completed',count=len(prompts),questions_sha256=runner.sha(packet),decoding=dict(enable_thinking=thinking)))
            (dest/'answers.jsonl').write_text(''.join(json.dumps(dict(r,raw_output='1<|im_end|>',generated_tokens=1,finish_reason='eos'))+'\n' for r in prompts),encoding='utf-8')
            jobs.append((str(dest),len(prompts),thinking))
        with tempfile.TemporaryDirectory() as temporary,patch.object(runner,'OUT',Path(temporary)),patch.object(runner.subprocess,'run',fake_subprocess):
            runner.dump(runner.OUT/'prompt-audit.json',dict(status='passed'))
            runner.run();self.assertEqual(len(jobs),7);self.assertEqual(sum(n for _,n,_ in jobs),266)
            self.assertEqual(sum(n for _,n,on in jobs if on),48)
            self.assertEqual(runner.read(runner.OUT/'completion.json')['outputs'],264)
            runner.run();self.assertEqual(len(jobs),7)
            bad=runner.OUT/'inference/thinking-on/base/manifest.json';m=runner.read(bad);m['decoding']['enable_thinking']=False;runner.dump(bad,m)
            with self.assertRaises(AssertionError):runner.run()

    def test_download_verifies_manifest_and_output_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);runtime=root/'experiments/stage-local';runtime.mkdir(parents=True)
            key=root/'dummy-test-key';key.write_text('test fixture, never sent to SSH')
            files={}
            def add(relative,value):
                p=runtime/relative;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(value);files[p.relative_to(root).as_posix()]=hashlib.sha256(value).hexdigest()
            add('completion.json',json.dumps(dict(status='completed',outputs=264,training_performed=False)).encode())
            for mode,n in [('main-off',72),('thinking-on',16)]:
                for model in ['base','cpt','cpt-bilingual69']:
                    add(f'inference/{mode}/{model}/manifest.json',json.dumps(dict(status='completed',count=n)).encode())
                    add(f'inference/{mode}/{model}/answers.jsonl',''.join(json.dumps(dict(id=str(i),raw_output='answer'))+'\n' for i in range(n)).encode())
            manifest=runtime/'backup-manifest.json';manifest.write_text(json.dumps(files))
            archive=runtime/'stage-diagnostic-artifacts.tar.gz'
            with tarfile.open(archive,'w:gz') as t:
                for name in list(files)+[manifest.relative_to(root).as_posix()]:t.add(root/name,arcname=name)
            metadata=dict(path='/workspace/stage-diagnostic-artifacts.tar.gz',contains_full_weights=False,
                          sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
            def fake_ssh(command,**kwargs):
                return json.dumps(metadata).encode() if command[-1]=='cat /workspace/stage-diagnostic-package.json' else b'ALL_DONE\n'
            argv=['script','download','--host','example.org','--port','2222','--key',str(key)]
            with patch.object(client,'ROOT',root),patch.object(client,'RUN',runtime),patch.object(client.subprocess,'check_output',fake_ssh),patch.object(fetch,'main',lambda:None),patch.object(sys,'argv',argv):
                client.main()
            receipt=json.loads((runtime/'LOCAL-BACKUP-RECEIPT.json').read_text())
            self.assertTrue(receipt['pod_safe_to_close']);self.assertEqual(receipt['files_verified'],13)

if __name__=='__main__':unittest.main()
