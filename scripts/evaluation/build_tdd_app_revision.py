"""Build reviewable framing-B records; never exports approved SFT rows."""
import argparse
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v03'
TOKENIZER=Path('/Users/cbarkinozer/Documents/llm-bender-artifacts/occam-gguf-20261026/base')
SYSTEM='''Prepare tests before implementing a Python application. Work from the request and the explicitly supplied preparation constraints. Produce five sections: Decisions and unresolved questions; Proposed interface agreement; Requirement-to-test map; Complete test files; Manual checks. Choose and explicitly document a minimal public interface; do not pretend the user specified your API names or defaults. Any necessary proposed behavior must be visible in the agreement. Leave nonessential unresolved choices open. Write compact pytest tests with all fixtures/configuration; Python standard library and declared dependencies only. Test observable contracts with deterministic offline fixtures, concrete justified expected results and useful assertions. Put subjective/live checks separately. Account for every requirement without claiming a narrow subset completes the app. Do not implement the app. Keep the accompanying rationale concise and focused on expected outcomes and coverage.'''
PREPARATION='''Preparation constraints for this demo (assistant-authored, not historical user answers): use Python and pytest. External services and model backends must be replaceable with offline fixtures; do not download weights or launch inference. The target proposes its own interface before tests. API names in that proposal are design choices, not facts recoverable from this paragraph. Repository source and validation evidence are review-only, absent from model input.'''
RATIONALES={
'github-insignia':'Public owned nonfork repositories with 5 and 9 stars total 14; 500 Rust bytes out of 800 yield 62.5%. Fixed UTC dates make calendar boundaries reproducible. Offline REST and GraphQL fixtures distinguish missing contributions from genuine zero, exercise pagination and preserve a previous snapshot after refresh failure. HTTP and MCP must expose the same stored data. Cache schema and credential checks protect observable state, while browser appearance and live authentication remain separate checks.',
'ghost-box':'Downloaded mail is a limited local corpus, so an empty search retains its coverage rather than asserting global absence. Account switching and clearing must invalidate both stored results and delayed callbacks. Combined filters and selected-only inference protect source provenance. A fake monotonic clock distinguishes 299.99 seconds from the 300-second idle boundary without sleeping; a fake model checks reuse and unload without loading weights. Real sign-in, native-window responsiveness and summary factuality remain unresolved/live checks.',
'slm_test_generation':'A passing pytest exit status alone is insufficient: skipped, uncalled and untaken assertions provide no reached oracle. Exact equality is strong even when its expected value is wrong, and execution failure must disable success gates. The fixture runner derives its gate from actual pytest outcomes. One successful observation among four eligible tasks is 25%, even with two observations missing. One killed mutant out of four eligible and two valid tasks gives 25% unconditional and 50% conditional; empty denominators are unavailable. Fresh fixtures avoid frozen benchmark instances.',
'llm-bender-lab':'Preflight must run before a trainer is called, so malformed conversations and overlapping prompts use a spy backend. A tiny trainer writes a real fixture adapter, and an evaluator records held-out rows/settings to establish matched comparison. A change from .5 to .75 is +.25; an unavailable metric remains unavailable. Exclusive run directories preserve earlier artifacts. A deliberate backend failure checks persistent failed status and sanitized logs without producing a success summary.',
'reflexmodels':'Two logits differing by 2 give softmax probabilities about .880797 and .119203, attached to the original Unicode option IDs. Invalid probabilities must fail before routing. Fallback depends separately on margin and answerability. Predictions that never select one class still need that class in macro-F1; accuracy .5 is compatible with macro-F1 1/3. Correct .75-confidence predictions have NLL -log(.75), Brier .125 and calibration error .25. Empty metric inputs raise an explicit error.',
'codelang-detect':'The unknown cases contain no supported code markers. Controlled regex configuration separates weighted scoring from match counting: weight 3 must beat two matches of weight 1. Equal scores need a declared deterministic tie rule. File and stdin routes must print exactly one label; input failures need useful stderr and a nonzero exit without a traceback. These fresh examples certify the stated starter contracts, not every language or ambiguous snippet.',
'repo-context':'The fixture checkout includes selected content, ignored content, a secret and an escaping symlink, so inclusion and exclusion are observable together. A one-line limit must include the first line, omit the second and disclose truncation. Exact metadata/dependency examples test truthful content, while cleanup is checked on success and clone failure. CLI/UI controller wrappers share one operation; actual UI wiring and private authentication still need a live check. Slash-containing branch ambiguity remains open rather than guessed.',
'cryptocurrency-analyser':'Prices 100,150,75 give cumulative returns 0,.5,-.25; they are not daily percentage changes. Interior missing values remain missing and only entirely missing series are omitted. Oppositely moving price series have correlation -1. CSV and provider inputs must yield the same values and dates, without requiring pandas inferred frequency metadata. Invalid selections fail before fetch; zero/missing baseline rejection is an explicit proposed policy. Provider failure never becomes a zero-return chart.',
'miniature-llms':'For [3,4], RMS is sqrt(12.5), so learned scales [2,3] produce [6,12]/sqrt(12.5). Position-zero RoPE is identity for every head and position-one rotation is determined by sequence, not head index. Shape checks alone cannot establish causal behavior, so future tokens are changed while earlier logits must remain fixed. Numeric gradients, checkpoint equality and repeatable CPU training test independent contracts. A controlled logit fixture uniquely predicts successor IDs, so prompt [1] must continue as [1,2,3,4]; length alone would allow a constant generator. Loss improvement is only a bounded smoke check, not proof of general model quality.'}
# Explicit semantic associations. Tooling validates identifiers; it does not infer coverage.
MAPS={
'github-insignia':[
 ('r1_', ['R1']),('r2_',['R2']),('r3_',['R3']),('r4_',['R4']),('r5_',['R3','R4','R6']),('r6_',['R5']),('r7_',['R4','R5','R6']),('r8_',['R5']),('r9_',['R6']),
 ('actual_transport',['R4','R6']),('graphql_http',['R4','R5','R6']),('real_zero',['R3']),('pagination_cannot',['R4','R6']),('corrupt_cache',['R5']),('missing_graphql',['R3','R4']),('http_mcp',['R6']),('structurally_invalid',['R5']),('authenticated_snapshot',['R3','R5'])],
'ghost-box':[
 ('session_mail',['R1','R5']),('clear_removes_mail',['R5']),('search_respects',['R2']),('literal_sender',['R2']),('long_mail',['R3']),('task_cap',['R3']),('summary_quote',['R3']),('explicit_fetch',['R1','R2']),('combined_search',['R2','R3']),('cancelled_or',['R4','R5']),('clear_removes_derived',['R5','R6'])],
'slm_test_generation':[
 ('oracle_strength',['R3']),('uncalled',['R2']),('reached_strong',['R2']),('trivial_pass',['R2']),('wrong_exact',['R2','R3']),('pytest_execution',['R1','R2','R3']),('runner_retains',['R1','R2','R6']),('passing_empty',['R1','R2']),('skipped_empty',['R1','R2']),('runner_preserves_timeout',['R1','R2']),('unsafe_task',['R6']),('nonpositive_timeout',['R1','R6']),('duplicate_eligible',['R4']),('aggregation',['R4']),('mutation_denominators',['R5']),('manifest_roundtrip',['R6']),('valid_docstring',['R1','R2'])],
'llm-bender-lab':[
 ('malformed_data',['R1']),('smoke_run',['R2','R4','R6']),('run_directories',['R3']),('invalid_preflight',['R1']),('failure_is',['R5','R6'])],
'reflexmodels':[
 ('runtime_unicode',['R1']),('invalid_decision',['R1']),('logits_map',['R2']),('invalid_probabilities',['R3']),('shared_state',['R4']),('low_margin',['R5']),('low_answerability',['R5']),('metrics_include',['R6']),('calibration_metrics',['R6']),('undefined_metrics',['R6'])],
'codelang-detect':[
 ('unknown_without',['R1']),('clear_language',['R3']),('weighted_evidence',['R2']),('equal_scores',['R2']),('cli_file',['R4']),('cli_stdin',['R4']),('missing_file',['R5']),('closed_stdin',['R5'])],
'repo-context':[
 ('tree_filters',['R2']),('explicit_ignore',['R2']),('requirements_are',['R3']),('pyproject_dependencies',['R3']),('branch_and',['R1']),('utf8',['R2']),('invalid_utf8',['R2']),('context_workflow',['R3','R4','R5']),('clone_failure',['R5']),('shared_operation',['R1','R2','R4','R5']),('cli_and_ui',['R6']),('invalid_url',['R1','R5'])],
'cryptocurrency-analyser':[
 ('returns_are',['R2']),('returns_preserve',['R2']),('missing_price',['R3']),('correlation_detects',['R4']),('fetch_drops',['R1','R3']),('combined_plot',['R4']),('comparator_normalizes',['R1','R4']),('saved_csv',['R1','R2','R5']),('provider_failure',['R1','R6']),('bad_selection',['R6']),('unusable_first',['R6'])],
'miniature-llms':[
 ('rmsnorm_uses',['R2']),('rmsnorm_epsilon',['R2']),('rmsnorm_backpropagates',['R2','R5']),('rotate_half',['R3']),('rope_position',['R3']),('rope_rotates',['R3']),('rope_rejects',['R1','R3']),('composed_model',['R1','R5']),('causal_outputs',['R4']),('checkpoint_roundtrip',['R5']),('deterministic_cpu',['R6']),('greedy_generation',['R6']),('negative_generation',['R6'])]}
APP_PREFIXES={
'github-insignia':('insignia',), 'ghost-box':('ghost_box','mail_workflow'),
'slm_test_generation':('oracle_analysis','benchmark_workflow'),
'llm-bender-lab':('experiment_workflow',), 'reflexmodels':('reflexmodels',),
'codelang-detect':('codelang_detect',), 'repo-context':('repo_context','context_workflow'),
'cryptocurrency-analyser':('coin_comparator','price_workflow'),
'miniature-llms':('_7_RMSNorm','_4_RoPE','tiny_model')}
EXTRA_MANUAL={
'github-insignia':['Verify documented startup commands from a clean checkout and capture desktop/mobile screenshots.'],
'ghost-box':['Verify Qt actually wires the proposed controller contracts to account switch, cancel and clear; check model selection for both MLX/GGUF.'],
'slm_test_generation':['Verify real network denial and process/memory isolation in the declared Docker image; tests prove fixture behavior, not adversarial sandbox security.','Check comparison-table/CLI documentation and run a fixture command; inspect output paths for frozen benchmark preservation. No reference module imports inference, but actual paper CLI wiring is not certified.'],
'llm-bender-lab':['Check prepare/run/compare commands and real trainer integration separately; tests supply an offline backend only.','Check .gitignore/publishing policy for credentials and large weights; backend persistence tests do not certify Git hygiene.'],
'reflexmodels':['Run the documented local request-to-response example; inspect uncertainty fields against the documented schema.'],
'codelang-detect':['Run installation and documented examples; additional supported languages require their own held-out accuracy evaluation.'],
'repo-context':['Wire actual CLI and Streamlit events to the shared operation, test generate/download parity and failure display. Wrapper tests alone do not establish that wiring.'],
'cryptocurrency-analyser':['Check actual browser sample-data option, data source/time labels and visible provider/baseline errors; the new reference API is not yet wired to the historical web UI.'],
'miniature-llms':['Run documented train/generate commands on CPU and check that the educational demo actually invokes the new tiny model; the historical repo has no such end-to-end CLI yet.']}
UNRESOLVED={
'github-insignia':['Visual theme and screenshot composition remain open.'],
'ghost-box':['Qt view layout and OAuth UX are not fixed by this contract; verify actual backend/progress integration separately.'],
'slm_test_generation':['Human semantic-correctness review rubric and production table layout remain open; UNKNOWN is never silently mapped to strong.'],
'llm-bender-lab':['Real training backend selection remains open; the demo only fixes its callable boundary.'],
'reflexmodels':['Production scoring model and acceptable calibration threshold require empirical selection.'],
'codelang-detect':['Accuracy expectations for ambiguous mixed-language snippets remain open.'],
'repo-context':['Slash-containing branch names need a separate branch argument or an unambiguous future URL syntax.'],
'cryptocurrency-analyser':['Live-provider UI retry/backoff behavior remains open.'],
'miniature-llms':['Tokenizer for a larger text corpus and real-language generation quality are out of this fixed token-fixture contract.']}


def main():
    global BUNDLE,SYSTEM,PREPARATION,RATIONALES,UNRESOLVED
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',choices=['app-core-v03','app-core-v04','app-core-v05'],default='app-core-v03')
    args=parser.parse_args()
    BUNDLE=BUNDLE.parent/args.revision
    version=args.revision.rsplit('-',1)[-1]
    config=json.loads((BUNDLE/'model-config.json').read_text()) if (BUNDLE/'model-config.json').exists() else {}
    if config:
        SYSTEM=config['system'];PREPARATION=config['preparation']
        RATIONALES=config['rationales'];UNRESOLVED=config['unresolved']
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(TOKENIZER,local_files_only=True,trust_remote_code=False)
    inputs=[json.loads(l) for l in (BUNDLE/'source-briefs.jsonl').read_text().splitlines()]
    runs={r['repo']:r for r in json.loads((BUNDLE/'token-and-execution-report.json').read_text())['reports']}
    for partial in BUNDLE.glob('execution-*.json'):
        if partial.name.startswith('execution-receipt'):continue
        for run in json.loads(partial.read_text())['reports']:runs[run['repo']]=run
    faults=json.loads(Path(json.loads((BUNDLE/'fault-receipt.json').read_text())['results']).read_text())
    records=[]
    for task in inputs:
        identifier=task['id']; folder=BUNDLE/identifier; run=runs[task['repo']]
        for file in run['files']+run['reference_files']:
            assert sha256((folder/file['path']).read_bytes()).hexdigest()==file['sha256'], 'Execution snapshot stale: '+file['path']
        interface=(folder/'interface.md').read_text()
        requirements=[dict(id=r['id'],text=r['requirement'],check_mode='automated-core',test_ids=[],manual_ids=[],coverage_status='mapped; semantic coverage requires review') for r in task['requirements']]
        req={r['id']:r for r in requirements}; tests=[]; imports=set()
        for file in sorted((folder/'tests').rglob('*.py')):
            tree=ast.parse(file.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith(APP_PREFIXES[identifier]):
                    for alias in node.names:imports.add((node.module,alias.name))
                if isinstance(node,ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(APP_PREFIXES[identifier]):imports.add((alias.name,'*'))
            for node in tree.body:
                if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or not node.name.startswith('test_'):continue
                tid=str(file.relative_to(folder))+'::'+node.name
                override=config.get('test_requirement_overrides',{}).get(identifier,{}).get(tid)
                matches=[override] if override is not None else [rs for prefix,rs in MAPS[identifier] if node.name[5:].startswith(prefix)]
                if not matches:raise ValueError(f'Unmapped test: {identifier}:{node.name}')
                ids=sorted(set(sum(matches,[])))
                tid=str(file.relative_to(folder))+'::'+node.name
                tests.append(dict(id=tid,requirements=ids))
                for rid in ids:req[rid]['test_ids'].append(tid)
        assert all(r['test_ids'] for r in requirements),identifier
        if version=='v05':
            from tdd_review_prechecks import check_test_numbering
            assert not check_test_numbering(tests), check_test_numbering(tests)
        # An exhaustive app import inventory supplements (not replaces) the prose contract.
        inventory='\n'.join('- `'+module+('` (module)' if name=='*' else '.'+name+'`') for module,name in sorted(imports))
        agreement=interface+('\nPublic imports:\n' if version in ('v04','v05') else '\nDeclared application import inventory (checked against test AST):\n')+inventory+'\n'
        manual=[dict(id=f'M{i+1}',text=text) for i,text in enumerate(config['manual_overrides'][identifier] if config else task['manual_checks']+EXTRA_MANUAL[identifier])]
        # Manual checks are adjuncts, never substitutions for missing backend coverage.
        decisions=('Proposed decisions:\n\n' if version in ('v04','v05') else 'These are assistant-proposed design choices for this demo, not recorded human answers.\n\n')+ '\n'.join('- '+d for d in task['assistant_decisions'] if 'unresolved behavior gaps' not in d and 'not yet represented' not in d)+'\n\nUnresolved/nonessential choices:\n'+'\n'.join('- '+d for d in UNRESOLVED[identifier])
        requirements.append(dict(id='R7' if len(requirements)==6 else 'R6',text='Usable delivery, documented commands and the declared live/manual integration checks.',check_mode='manual-or-live-integration',test_ids=[],manual_ids=[m['id'] for m in manual],coverage_status='explicitly pending; not certified by backend tests'))
        mapping='\n\n'.join(r['id']+': '+r['text']+'\n'+'\n'.join('- `'+t+'`' for t in r['test_ids'])+('\nManual/live: '+', '.join(r['manual_ids']) if r['manual_ids'] else '') for r in requirements)
        manual_text='\n'.join(m['id']+': '+m['text'] for m in manual)
        target='## Decisions and unresolved questions\n\n'+decisions+'\n\n## Proposed interface agreement\n\n'+agreement+'\n## Requirement-to-test map\n\n'+mapping+'\n\n## Complete test files\n\n'+(folder/'test-output.md').read_text()+'\n## Manual checks\n\n'+manual_text+'\n'
        messages=[{'role':'system','content':SYSTEM+('\n\n'+PREPARATION if version in ('v04','v05') else '')},{'role':'user','content':task['user_request']+('' if version in ('v04','v05') else '\n\n'+PREPARATION)},
                  {'role':'assistant','reasoning_content':RATIONALES[identifier],'content':target}]
        sections=['Decisions and unresolved questions','Proposed interface agreement','Requirement-to-test map','Complete test files','Manual checks']
        positions=[target.index('## '+section+'\n') for section in sections]
        assert positions==sorted(positions) and all(target.count('## '+section+'\n')==1 for section in sections)
        ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=False,enable_thinking=True)
        if isinstance(ids, dict) or hasattr(ids,'keys'): ids=ids['input_ids']
        assert isinstance(ids,list) and all(isinstance(i,int) for i in ids)
        rendered=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=False,enable_thinking=True)
        assert '<think>\n'+RATIONALES[identifier] in rendered and '</think>' in rendered
        assert len(ids)>=len(tokenizer.encode(target,add_special_tokens=False)), 'Full sequence cannot be shorter than the target'
        assert len(ids)==len(tokenizer.encode(rendered,add_special_tokens=False)), 'Serialized text and template token counts disagree'
        stability_report=json.loads(Path(json.loads((BUNDLE/'stability-receipt.json').read_text())['results']).read_text())
        stable=[r for r in stability_report['results'] if r['repo']==task['repo']]
        per_req_faults={r['id']:[f['fault'] for f in faults['results'] if f['repo']==task['repo'] and f['killed'] and r['id'] in f['target_requirements'] and any(node.split('[')[0].endswith(t['id']) and r['id'] in t['requirements'] for node in f['failing_tests'] for t in tests)] for r in requirements if r['check_mode']=='automated-core'}
        assert all(per_req_faults.values()), (identifier,per_req_faults)
        assert len(stable)==3 and all(r['returncode']==0 for r in stable)
        collected={node.split('[')[0] for node in stable[0]['order']}
        assert all(any(node.endswith(t['id']) for node in collected) for t in tests), 'Mapped test was not collected'
        assert all(any(node.endswith(t['id']) for t in tests) for node in collected), 'Collected test is unmapped'
        preservation=[]
        for check in config.get('preservation_checks',{}).get(identifier,[]):
            for label in check['faults']:
                match=[f for f in faults['results'] if f['repo']==task['repo'] and f['fault']==label]
                assert len(match)==1 and match[0]['killed'], (identifier,check)
                assert any(node.split('[')[0].endswith(t['id']) and check['requirement_id'] in t['requirements'] for node in match[0]['failing_tests'] for t in tests), (identifier,check)
            preservation.append(dict(check,detected=True))
        record=dict(record_id=identifier+'-'+version,schema_version='1.0',record_version=int(version[1:]),
            framing='request-to-proposed-interface-and-tests',status='awaiting-human-review',
            source=dict(repo=task['repo'],revision=run['source_commit'],dirty=run['source_dirty'],
                        origin=task['provenance']['origin'],new_reference_files=run['reference_files'],
                        reference_note='New workflow references are validation material; they do not prove those workflows are wired into the original app.'),
            split='eval' if identifier in ('github-insignia','slm_test_generation') else 'train',
            split_status='proposed; disjoint by repo; no training export',leakage_group=task['repo'],paper_benchmark_overlap='same-repository-and-taxonomy; no benchmark instances used' if identifier=='slm_test_generation' else 'no benchmark instances used; near-duplicate audit still pending',
            messages=messages,teacher_reasoning=RATIONALES[identifier],decisions=decisions,
            interface=dict(location='target-output',text=agreement,imports=[dict(module=m,name=n) for m,n in sorted(imports)]),
            requirements=requirements,test_registry=tests,manual_checks=manual,
            validation=dict(reference_pass=run['returncode']==0,execution_log=run['log'],
                            test_files=run['files'],faults=[f for f in faults['results'] if f['repo']==task['repo']],
                            structural_map_consistency=True,semantic_map_approval=False,
                            test_numbering_consistent=(version=='v05'),preservation_checks=preservation,
                            fault_coverage_by_core_requirement=per_req_faults,all_core_requirements_have_killed_variant=True,
                            stability=stable,three_order_runs_pass=True,
                            interface_import_consistency=True,interface_attribute_and_schema_review='manual; import presence alone is insufficient',
                            smoke_only=True,full_original_app_certified=False),
            tokens=dict(full_sequence=len(ids),limit=8192,within_limit=len(ids)<=8192,
                        per_section={name:len(tokenizer.encode(value,add_special_tokens=False)) for name,value in
                                     dict(system=messages[0]['content'],user=messages[1]['content'],reasoning=RATIONALES[identifier],interface=agreement,tests=(folder/'test-output.md').read_text(),target=target).items()},
                        tokenizer_sha256=sha256((TOKENIZER/'tokenizer.json').read_bytes()).hexdigest(),
                        chat_template_sha256=sha256((TOKENIZER/'chat_template.jinja').read_bytes()).hexdigest(),
                        note='Actual native chat serialization including reasoning and EOS; section counts need not add exactly to full sequence.'),
            provenance=dict(drafter='OpenAI Codex session assistant; exact model build not exposed',date=(json.loads((folder/'record.json').read_text())['provenance']['date'] if (folder/'record.json').exists() else datetime.now(timezone.utc).isoformat()),prompt_version='tdd-framing-b-'+version,reviewer=None,review_history=[],
                            source_informed=True,not_historical_zero_shot_prompt=True),
            tags=dict(domain=task['repo'],difficulty='unrated',component_type='whole-app acceptance core',external_services_faked=True),
            training_eligible=False)
        if version in ('v04','v05'):
            from scan_tdd_model_text import scan_record
            findings=scan_record(record)
            assert all(f['status']=='allowed' for f in findings), (identifier,findings)
            record['validation']['model_text_scan']={'findings':findings,'unresolved':0,'note':'Lexical construction-context check, not a scientific contamination proof.'}
        (folder/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        (folder/'request.md').write_text(messages[1]['content']+'\n')
        (folder/'target.md').write_text(target)
        (folder/'reasoning.md').write_text(RATIONALES[identifier]+'\n')
        records.append(record)
        print(task['repo'],len(ids),'tokens',flush=True)
    assert len(records)==9
    assert not ({r['leakage_group'] for r in records if r['split']=='train'} & {r['leakage_group'] for r in records if r['split']=='eval'})
    (BUNDLE/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    report=dict(records=len(records),all_reference_pass=all(r['validation']['reference_pass'] for r in records),
                reference_cases=sum(len(r['validation']['stability'][0]['order']) for r in records),
                preservation_contracts=sum(len(r['validation'].get('preservation_checks',[])) for r in records),
                test_numbering_consistent=all(r['validation']['test_numbering_consistent'] for r in records),
                construction_text_unresolved=sum(r['validation'].get('model_text_scan',{}).get('unresolved',0) for r in records),
                targeted_faults=sum(len(r['validation']['faults']) for r in records),
                core_requirements=sum(len(r['validation']['fault_coverage_by_core_requirement']) for r in records),
                all_within_8192=all(r['tokens']['within_limit'] for r in records),
                maximum_tokens=max(r['tokens']['full_sequence'] for r in records),
                total_tokens=sum(r['tokens']['full_sequence'] for r in records),
                train_candidates=[r['record_id'] for r in records if r['split']=='train'],
                heldout_repos=[r['source']['repo'] for r in records if r['split']=='eval'],
                no_training_exports=True,all_requirements_mapped=True,all_core_requirements_have_killed_variant=True,all_three_order_runs_pass=True,
                manual_approval_pending=True,scope_limit='Backend contracts plus explicitly pending delivery/live checks; not nine certified original apps.',records_sha256=sha256((BUNDLE/'records.jsonl').read_bytes()).hexdigest())
    (BUNDLE/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
