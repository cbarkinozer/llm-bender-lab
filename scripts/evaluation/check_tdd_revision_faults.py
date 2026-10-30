"""Targeted fault probes for trusted v03 suites; sources are never mutated."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v03'
ART=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts')
PYTHON=ART/'occam-gguf-20261026/.venv/bin/python'
DEPS=ART/'thinking-tdd/repo-audit-20261030/deps'
FAULTS={
'GitHub-insignia':{
 'wrong-star-total':"import insignia.metrics as m\noriginal=m.repository_metrics\ndef broken(*a,**k):\n    return original(*a,**k)|{'stars':0}\nm.repository_metrics=broken",
 'wrong-sort-order':"import insignia.metrics as m\noriginal=m.top_repositories\nm.top_repositories=lambda *a,**k:list(reversed(original(*a,**k)))"},
'ghost-box':{
 'apply-cancelled-result':"from mail_workflow import MailApp\ndef broken(self,op,result):\n    self.result=result\n    return True\nMailApp.finish=broken",
 'never-unload-idle-model':"from mail_workflow import MailApp\nMailApp.check_idle=lambda self:None"},
'slm_test_generation':{
 'ignore-reachability':"import oracle_analysis as m\noriginal=m.gate_outcomes\nm.gate_outcomes=lambda passed,sites,reached:original(passed,sites,{s.oracle_id for s in sites})",
 'weak-is-strong':"import oracle_analysis as m\nfrom dataclasses import replace\noriginal=m.classify_oracles\nm.classify_oracles=lambda *a,**k:[replace(s,oracle_class=m.OracleClass.STRONG) if s.oracle_class is m.OracleClass.WEAK else s for s in original(*a,**k)]",
 'ignore-suite-failure':"import oracle_analysis as m\noriginal=m.gate_outcomes\nm.gate_outcomes=lambda passed,sites,reached:original(True,sites,reached)"},
'llm-bender-lab':{
 'missing-metrics-become-zero':"import experiment_workflow as m\noriginal=m.run_experiment\ndef broken(*a,**k):\n    result=original(*a,**k)\n    if result['status']=='completed':\n        for metric in result['comparison'].values():\n            if metric['delta'] is None: metric['delta']=0\n    return result\nm.run_experiment=broken",
 'allow-overwrite':"import experiment_workflow as m\noriginal=m.run_experiment\nfrom pathlib import Path\nimport shutil\ndef broken(root,name,*a,**k):\n    shutil.rmtree(Path(root)/name,ignore_errors=True)\n    return original(root,name,*a,**k)\nm.run_experiment=broken"},
'ReflexModels':{
 'f1-equals-accuracy':"import reflexmodels.metrics as m\noriginal=m.classification_metrics\ndef broken(*a,**k):\n    result=original(*a,**k)\n    result['macro_f1']=result['accuracy']\n    return result\nm.classification_metrics=broken",
 'ignore-margin':"import reflexmodels as m\noriginal=m.fallback_gate\ndef broken(*a,**k):\n    k['min_margin']=0\n    return original(*a,**k)\nm.fallback_gate=broken"},
'codelang-detect':{
 'ignore-rule-weights':"import codelang_detect.detector as m\noriginal=m.detect\ndef broken(text):\n    rules=m.PATTERNS\n    try:\n        m.PATTERNS={key:[(pattern,1) for pattern,weight in values] for key,values in rules.items()}\n        return original(text)\n    finally:m.PATTERNS=rules\nm.detect=broken\nimport codelang_detect\ncodelang_detect.detect=broken",
 'extra-cli-output':"import codelang_detect.cli as m\noriginal=m.main\ndef broken():\n    original()\n    print('unknown')\nm.main=broken"},
'repo-context':{
 'leak-token':"import context_workflow as m\noriginal=m.snapshot\nm.snapshot=lambda *a,**k:original(*a,**k)+(k.get('token') or '')",
 'never-clean-checkout':"import context_workflow as m\nm.shutil.rmtree=lambda *a,**k:None"},
'cryptocurrency-analyser':{
 'daily-instead-of-cumulative':"import coin_comparator as m\nm.calculate_cumulative_returns=lambda prices:prices.pct_change(fill_method=None).fillna(0)",
 'zero-fill-missing-prices':"import coin_comparator as m\noriginal=m.calculate_cumulative_returns\nm.calculate_cumulative_returns=lambda prices:original(prices.fillna(0))"},
'miniature-llms':{
 'remove-causal-mask':"import tiny_model as m\noriginal=m.F.scaled_dot_product_attention\ndef broken(*a,**k):\n    k['is_causal']=False\n    return original(*a,**k)\nm.F.scaled_dot_product_attention=broken",
 'rotate-head-axis':"from _4_RoPE.pytorch import RoPE\noriginal=RoPE.forward\nRoPE.forward=lambda self,x:original(self,x.transpose(1,2)).transpose(1,2)"}}


TARGETS={
'GitHub-insignia':{'wrong-star-total':['R1'],'wrong-sort-order':['R2']},
'ghost-box':{'apply-cancelled-result':['R4'],'never-unload-idle-model':['R6']},
'slm_test_generation':{'ignore-reachability':['R2'],'weak-is-strong':['R3'],'ignore-suite-failure':['R2']},
'llm-bender-lab':{'missing-metrics-become-zero':['R6'],'allow-overwrite':['R3']},
'ReflexModels':{'f1-equals-accuracy':['R6'],'ignore-margin':['R5']},
'codelang-detect':{'ignore-rule-weights':['R2'],'extra-cli-output':['R4']},
'repo-context':{'leak-token':['R5'],'never-clean-checkout':['R5']},
'cryptocurrency-analyser':{'daily-instead-of-cumulative':['R2'],'zero-fill-missing-prices':['R3']},
'miniature-llms':{'remove-causal-mask':['R4'],'rotate-head-axis':['R3']}}
EXTRA={
'GitHub-insignia':{
 'shift-calendar-window':('R3',"import insignia.metrics as m\nfrom datetime import timedelta\noriginal=m.date_window\ndef broken(now):\n    start,end=original(now)\n    return start-timedelta(days=1),end\nm.date_window=broken"),
 'drop-pagination-link':('R4',"import insignia.github as m\noriginal=m.GitHubClient.fetch\nasync def broken(self,*a,**k):\n    handler=self.transport.handler\n    def no_link(request):\n        response=handler(request)\n        response.headers.pop('link',None)\n        return response\n    import httpx\n    self.transport=httpx.MockTransport(no_link)\n    return await original(self,*a,**k)\nm.GitHubClient.fetch=broken"),
 'skip-cache-write':('R5',"from insignia.service import DashboardService\nDashboardService._save=lambda *a,**k:None"),
 'mcp-summary-has-stale-timestamp':('R6',"from insignia.service import DashboardService\noriginal=DashboardService.summary\nDashboardService.summary=lambda self:original(self)|{'fetched_at':'2000-01-01T00:00:00+00:00'}")},
'ghost-box':{
 'fetch-wrong-account':('R1',"from mail_workflow import MailApp\noriginal=MailApp.fetch\ndef broken(self,*a,**k):\n    self.account='wrong-account'\n    return original(self,*a,**k)\nMailApp.fetch=broken"),
 'ignore-sender-filter':('R2',"from mail_workflow import MailApp\noriginal=MailApp.search\ndef broken(self,*a,**k):\n    k['sender']=''\n    return original(self,*a,**k)\nMailApp.search=broken"),
 'send-entire-inbox-to-model':('R3',"from mail_workflow import MailApp\noriginal=MailApp.answer\nMailApp.answer=lambda self,ids,question:original(self,[m['id'] for m in self._mail],question)"),
 'clear-keeps-derived-result':('R5',"from mail_workflow import MailApp\noriginal=MailApp.clear\ndef broken(self):\n    previous=self.result\n    original(self)\n    self.result=previous\nMailApp.clear=broken")},
'slm_test_generation':{
 'collapse-execution-outcomes':('R1',"import benchmark_workflow as m\noriginal=m.run_task\ndef broken(*a,**k):\n    return original(*a,**k)|{'outcome':'passed'}\nm.run_task=broken"),
 'observed-instead-of-eligible-denominator':('R4',"import benchmark_workflow as m\noriginal=m.summarize\ndef broken(*a,**k):\n    result=original(*a,**k)\n    result['success_rate']=result['successful']/result['observed'] if result['observed'] else None\n    return result\nm.summarize=broken"),
 'conditional-uses-eligible':('R5',"import benchmark_workflow as m\noriginal=m.mutation_summary\ndef broken(*a,**k):\n    result=original(*a,**k)\n    result['conditional']=result['unconditional']\n    return result\nm.mutation_summary=broken"),
 'manifest-loses-seed':('R6',"import benchmark_workflow as m\noriginal=m.save_manifest\nm.save_manifest=lambda path,manifest:original(path,{k:v for k,v in manifest.items() if k!='seed'})")},
'llm-bender-lab':{
 'normalize-away-invalid-conversation':('R1',"import experiment_workflow as m\nfrom copy import deepcopy\noriginal=m.run_experiment\ndef broken(root,name,config,rows,**k):\n    rows=deepcopy(rows)\n    for i,row in enumerate(rows):\n        row['split']='train' if i==0 else 'test'\n        row['messages']=[{'role':'user','content':str(i)},{'role':'assistant','content':'5'}]\n    return original(root,name,config,rows,**k)\nm.run_experiment=broken"),
 'resolved-config-loses-seed':('R2',"import experiment_workflow as m\nfrom pathlib import Path\nimport json\noriginal=m.run_experiment\ndef broken(root,name,*a,**k):\n    result=original(root,name,*a,**k)\n    path=Path(root)/name/'resolved.json'\n    data=json.loads(path.read_text());data['seed']=0;path.write_text(json.dumps(data))\n    return result\nm.run_experiment=broken"),
 'empty-adapter-artifact':('R4',"import experiment_workflow as m\nfrom pathlib import Path\noriginal=m.run_experiment\ndef broken(root,name,*a,**k):\n    result=original(root,name,*a,**k)\n    path=Path(root)/name/'adapter.bin'\n    if path.exists():path.write_bytes(b'')\n    return result\nm.run_experiment=broken"),
 'backend-failure-claims-success':('R5',"import experiment_workflow as m\noriginal=m.run_experiment\ndef broken(*a,**k):\n    result=original(*a,**k)\n    if result['status']=='failed':result['status']='completed'\n    return result\nm.run_experiment=broken")},
'ReflexModels':{
 'request-loses-original-option-ids':('R1',"import reflexmodels.protocol as m\nimport json\noriginal=m.request_to_json\ndef broken(*a,**k):\n    row=json.loads(original(*a,**k));row['options']={'wrong':'option'};return json.dumps(row)\nm.request_to_json=broken"),
 'select-wrong-option':('R2',"import reflexmodels as m\noriginal=m.score_decision\ndef broken(*a,**k):\n    result=original(*a,**k);result['selected_option']='web';return result\nm.score_decision=broken"),
 'accept-invalid-probabilities':('R3',"import reflexmodels as m\nm.choice_response=lambda *a,**k:{'selected_option':'files','option_probabilities':k['probabilities']}"),
 'mix-shared-question-options':('R4',"import reflexmodels as m\noriginal=m.score_shared_state\ndef broken(*a,**k):\n    result=original(*a,**k);result['continue']=result['tool'];return result\nm.score_shared_state=broken")},
'codelang-detect':{
 'empty-input-is-python':('R1',"import codelang_detect as m\noriginal=m.detect\nm.detect=lambda text:'py' if not text.strip() else original(text)"),
 'swap-starter-language-label':('R3',"import codelang_detect as m\noriginal=m.detect\ndef broken(text):\n    result=original(text);return 'js' if result=='py' else result\nm.detect=broken"),
 'swallow-input-errors':('R5',"import codelang_detect.cli as m\noriginal=m.main\ndef broken():\n    try:return original()\n    except SystemExit as exc:\n        if exc.code==0:raise\nm.main=broken")},
'repo-context':{
 'ignore-requested-branch':('R1',"import repo_context.core as m\noriginal=m.parse_github_url\ndef broken(url):\n    base,branch,sub=original(url);return base,'main',sub\nm.parse_github_url=broken"),
 'ignore-gitignore-policy':('R2',"import context_workflow as m\nm.parse_gitignore=lambda path:lambda file:False"),
 'omit-dependency-summary':('R3',"import repo_context.core as m\nm.analyze_dependencies=lambda root:('Python','')"),
 'ignore-line-limit':('R4',"import context_workflow as m\noriginal=m.snapshot\ndef broken(*a,**k):\n    k['line_limit']=0;return original(*a,**k)\nm.snapshot=broken"),
 'ui-does-not-use-shared-operation':('R6',"import context_workflow as m\nm.ui_snapshot=lambda *a,**k:'stale preview'")},
'cryptocurrency-analyser':{
 'provider-receives-lowercase-symbols':('R1',"import price_workflow as m\noriginal=m.analyze\ndef broken(*a,**k):\n    if k.get('provider') is not None:\n        provider=k['provider'];k['provider']=lambda symbols,start,end:provider([s.lower() for s in symbols],start,end)\n    return original(*a,**k)\nm.analyze=broken"),
 'correlation-always-zero':('R4',"import coin_comparator as m\noriginal=m._calculate_correlation\nm._calculate_correlation=lambda prices:original(prices)*0"),
 'csv-source-mislabeled':('R5',"import price_workflow as m\noriginal=m.analyze\ndef broken(*a,**k):\n    return original(*a,**k)|{'source':'provider'}\nm.analyze=broken"),
 'silently-repair-invalid-baseline':('R6',"import price_workflow as m\noriginal=m.analyze\ndef broken(*a,**k):\n    if k.get('provider') is not None:\n        provider=k['provider']\n        def repaired(*args):\n            frame=provider(*args).copy();row=frame.iloc[0];frame.iloc[0]=row.mask(row.isna()|(row==0),1);return frame\n        k['provider']=repaired\n    return original(*a,**k)\nm.analyze=broken")},
'miniature-llms':{
 'wrong-logit-vocabulary-dimension':('R1',"from tiny_model import TinyModel\noriginal=TinyModel.forward\nTinyModel.forward=lambda self,tokens:original(self,tokens)[...,:-1]"),
 'rmsnorm-ignores-learned-scale':('R2',"from _7_RMSNorm.pytorch import RMSNorm\noriginal=RMSNorm.forward\nRMSNorm.forward=lambda self,x:original(self,x)/self.weight"),
 'checkpoint-loses-weights':('R5',"from tiny_model import TinyModel\nimport torch\noriginal=TinyModel.load\ndef broken(cls,path):\n    result=original(path)\n    with torch.no_grad():\n        for p in result.parameters():p.zero_()\n    return result\nTinyModel.load=classmethod(broken)"),
 'generation-exceeds-token-budget':('R6',"import tiny_model as m\noriginal=m.generate\nm.generate=lambda model,prompt,**k:original(model,prompt,max_new_tokens=k['max_new_tokens']+1)")}}
EXTRA['slm_test_generation']['break-valid-module-header']=('R1',"import oracle_analysis as m\nfrom step4_evaluation.oracle_analysis import instrument_oracles\nm.instrument_oracles=instrument_oracles")
EXTRA['miniature-llms']['constant-generated-tokens']=('R6',"import tiny_model as m\nm.generate=lambda model,prompt,**k:list(prompt)+[0]*k['max_new_tokens']")
for repo,extra in EXTRA.items():
    for name,(requirement,code) in extra.items():
        FAULTS[repo][name]=code
        TARGETS[repo][name]=[requirement]


PRESERVATION_FAULTS = {
'GitHub-insignia':{
 'timestamp-changes-on-failed-refresh':('R5',"from insignia.service import DashboardService\nfrom datetime import datetime,timedelta\noriginal=DashboardService.refresh\nasync def broken(self):\n    result=await original(self)\n    if result['error'] and self.snapshot is not None:\n        self.snapshot['fetched_at']=(datetime.fromisoformat(self.snapshot['fetched_at'])+timedelta(seconds=1)).isoformat()\n    return self.read()\nDashboardService.refresh=broken"),
 'memory-replaced-before-cache-save':('R5',"from insignia.service import DashboardService\nfrom insignia.github import GitHubError\nasync def broken(self):\n    async with self.lock:\n        try:\n            candidate=await self.api.fetch('cbarkinozer',self.clock())\n            self.snapshot=candidate\n            self._save(candidate)\n        except GitHubError as exc:self.error=str(exc)\n        except OSError:self.error='Could not save snapshot'\n        else:self.error=None\n        return self.read()\nDashboardService.refresh=broken"),
 'disk-overwritten-on-failed-refresh':('R5',"from insignia.service import DashboardService\nimport json\noriginal=DashboardService.refresh\nasync def broken(self):\n    result=await original(self)\n    if result['error'] and self.snapshot is not None:self.cache_path.write_text(json.dumps({'fetched_at':'corrupted'}))\n    return result\nDashboardService.refresh=broken"),
 'keep-old-snapshot-after-successful-refresh':('R5',"from insignia.service import DashboardService\noriginal=DashboardService.refresh\nasync def broken(self):\n    if self.snapshot is not None:return self.read()\n    return await original(self)\nDashboardService.refresh=broken")},
'slm_test_generation':{
 'raw-generation-overwritten-by-instrumentation':('R1',"import benchmark_workflow as m\nfrom pathlib import Path\noriginal=m.run_task\ndef broken(task,**kwargs):\n    result=original(task,**kwargs)\n    root=Path(kwargs['root'])/task['id']\n    (root/'generation.txt').write_text((root/'test_generated.py').read_text())\n    return result\nm.run_task=broken"),
 'missing-observations-erased':('R4',"import benchmark_workflow as m\noriginal=m.summarize\ndef broken(**kwargs):\n    result=original(**kwargs);result['missing']=0;return result\nm.summarize=broken")},
'llm-bender-lab':{
 'new-run-corrupts-older-adapter':('R3',"import experiment_workflow as m\nfrom pathlib import Path\noriginal=m.run_experiment\ndef broken(root,name,*args,**kwargs):\n    result=original(root,name,*args,**kwargs)\n    for folder in Path(root).iterdir():\n        if folder.name!=name and (folder/'adapter.bin').is_file():(folder/'adapter.bin').write_bytes(b'corrupted')\n    return result\nm.run_experiment=broken")},
'cryptocurrency-analyser':{
 'returns-mutate-input-prices':('R2',"import coin_comparator as m\noriginal=m.calculate_cumulative_returns\ndef broken(prices):\n    result=original(prices);prices.iloc[0,0]+=1;return result\nm.calculate_cumulative_returns=broken")}}
for repo,probes in PRESERVATION_FAULTS.items():
    for label,(rid,code) in probes.items():
        FAULTS[repo][label]=code;TARGETS[repo][label]=[rid]


def main():
    global BUNDLE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo')
    parser.add_argument('--revision',choices=['app-core-v03','app-core-v04','app-core-v05'],default='app-core-v03')
    args=parser.parse_args()
    BUNDLE=BUNDLE.parent/args.revision
    output=ART/('thinking-tdd/'+args.revision+'-faults')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    config=json.loads((BUNDLE/'model-config.json').read_text()) if (BUNDLE/'model-config.json').exists() else {}
    preservation_labels={key:{label for check in checks for label in check['faults']} for key,checks in config.get('preservation_checks',{}).items()}
    results=[]
    if args.repo and args.repo not in FAULTS: raise ValueError(args.repo)
    for repo, faults in FAULTS.items():
        if args.repo and repo!=args.repo: continue
        folder=BUNDLE/repo.lower(); source=ROOT.parent/repo
        for label,code in faults.items():
            target=output/repo/label;target.mkdir(parents=True)
            plugin=target/'fault_probe.py'
            plugin.write_text('import json\nfrom pathlib import Path\nFAILURES=[]\ndef pytest_configure(config):\n'+''.join('    '+line+'\n' for line in code.splitlines())+'\ndef pytest_runtest_logreport(report):\n    if report.failed: FAILURES.append(dict(nodeid=report.nodeid,when=report.when,detail=report.longreprtext))\ndef pytest_sessionfinish(session,exitstatus):\n    Path('+repr(str(target/'failures.json'))+').write_text(json.dumps(FAILURES,indent=2))\n')
            python=source/'.venv/bin/python' if repo in ('GitHub-insignia','ghost-box') else PYTHON
            paths=[str(target),str(folder/'reference'),str(source),str(source/'src'),str(DEPS)]
            env=dict(os.environ,PYTHONPATH=os.pathsep.join(paths),PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1')
            for key in list(env):
                if any(s in key.upper() for s in ('TOKEN','API_KEY','SECRET','PASSWORD')):env.pop(key)
            command=[str(python),'-m','pytest','-q','-p','fault_probe',str(folder/'tests')]
            if (folder/'pytest.ini').exists():command+=['-c',str(folder/'pytest.ini')]
            result=subprocess.run(command,cwd=source,env=env,capture_output=True,text=True,timeout=90)
            (target/'pytest.log').write_text(result.stdout+result.stderr)
            failures=json.loads((target/'failures.json').read_text()) if (target/'failures.json').exists() else []
            killed=result.returncode==1 and any(f['when']=='call' and ('AssertionError' in f['detail'] or 'Failed:' in f['detail']) for f in failures)
            results.append(dict(repo=repo,fault=label,target_requirements=TARGETS[repo][label],preservation_probe=label in preservation_labels.get(repo.lower(),set()) or label in PRESERVATION_FAULTS.get(repo,{}),killed=killed,returncode=result.returncode,
                                failing_tests=[f['nodeid'] for f in failures],log=str(target/'pytest.log'),
                                mutation_sha256=sha256(plugin.read_bytes()).hexdigest(),
                                test_snapshot={str(p.relative_to(folder)):sha256(p.read_bytes()).hexdigest() for p in sorted((folder/'tests').rglob('*.py'))}))
            print(repo,label,'KILLED' if killed else 'NOT VALIDATED',flush=True)
    if args.repo:
        previous=json.loads(Path(json.loads((BUNDLE/'fault-receipt.json').read_text())['results']).read_text())
        results=[r for r in previous['results'] if r['repo']!=args.repo]+results
    report=dict(results=results,all_killed=all(r['killed'] for r in results),
                note='Targeted fault probes, not exhaustive mutation coverage. Original checkouts unchanged.')
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (BUNDLE/'fault-receipt.json').write_text(json.dumps({'results':str(output/'results.json'),'all_killed':report['all_killed']},indent=2)+'\n')
    print(output)

if __name__=='__main__':main()
