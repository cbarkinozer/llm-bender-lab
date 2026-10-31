"""Recorded assistant semantic adjudications; scores are retrieval evidence only."""
from hashlib import sha256
import json
from pathlib import Path
import argparse
from active_tdd_data import EXP,active_paths,rows,read_json,inside

PAIRS=[
 ('tldr-python-client-backend-plan-planning-v04','tldr-python-client-backend-plan-offline-cache-planning-v04','expected_scoped_variant','The second request explicitly limits the first app to cache behavior. Large shared context is expected; this is not another independent app.'),
 ('repo-context-app-plan-planning-v04','repo-context-app-plan-snapshot-core-planning-v04','expected_scoped_variant','The focused plan selects tree/dependency/decoding work and defers delivery. Same family and split; substantial shared context warrants mixture control.'),
 ('ghost-box-app-plan-planning-v04','ghost-box-app-plan-first-memory-milestone-planning-v04','expected_scoped_variant','The RAM/search/splitting milestone is an explicit subset of the desktop app. Do not count it as a new independent source.'),
 ('litecli-backend-plan-planning-v04','litecli-backend-plan-sql-core-planning-v04','expected_scoped_variant','The focused request removes completion/dispatch tasks. This is a scope variant, not a second repository.'),
 ('ddgr-result-serialization-external-v02','ddgr-result-contract-reliability-v03','expected_cross_track_overlap','One writes schema assertions; the other decides that an explicit schema needs no clarification. Both remain holdout and derive from the same family.'),
 ('tldr-python-client-cache-network-routing-external-v02','tldr-python-client-backend-plan-offline-cache-planning-v04','expected_cross_track_overlap','The plan contains the child cache-routing task. That is intended hierarchy, not an independent task example.'),
 ('posting-query-pair-merge-external-v02','posting-backend-plan-planning-v04','expected_cross_track_overlap','The query-merging test task is explicitly part of the request-client plan, in development on both sides.'),
 ('posting-path-parameters-external-v02','ddgr-unicode-safe-urls-external-v02','distinct_contracts','Posting extracts/replaces colon placeholders only in URL paths and preserves escaped literals; ddgr performs IDNA and percent encoding of full URLs. Shared URL vocabulary is not the same oracle.'),
 ('tldr-python-client-page-url-external-v02','ddgr-unicode-safe-urls-external-v02','distinct_contracts','tldr constructs a language/platform page address and escapes a command. ddgr converts arbitrary hosts/credentials/path/query/fragment. Encoding is shared background skill; the task contracts differ.'),
 ('snapshot-url-routing-v02','posting-path-parameters-external-v02','distinct_contracts','Repository/ref/subfolder selection is different from path-variable extraction and substitution, despite both parsing URLs.'),
 ('litecli-path-completion-external-v02','posting-request-filenames-external-v02','distinct_contracts','Completion lists filesystem candidates and tracks cursor offsets. Request filename validation/collision handling proposes safe unique save names.'),
 ('litecli-sql-table-identifiers-external-v02','posting-query-pair-merge-external-v02','distinct_contracts','SQL tables/aliases and repeated HTTP query-parameter occurrences are different grammars and expected structures.'),
 ('tensor-checkpoint-roundtrip-v02','ddgr-result-serialization-external-v02','distinct_contracts','Model state/prediction preservation across checkpoint reload differs from exact JSON result fields and string index lookup.'),
 ('mail-cancellation-v02','posting-session-undo-redo-external-v02','distinct_contracts','Generation/account operation tokens reject stale async results. Session undo/redo restores editing history and invalidates branched redo. Both are stateful but have different transitions.'),
 ('language-basic-v02','posting-request-filenames-external-v02','distinct_contracts','Language labels and safe filenames have unrelated predicates. Positive/negative controls are a general testing technique, not a duplicate problem.'),
 ('returns-baseline-reliability-v03','posting-latency-reliability-v03','distinct_contracts','Clarifying which price defines a denominator is different from defining UI responsiveness versus remote completion. The shared ask action is the capability label.'),
 ('snapshot-secret-scope-reliability-v03','ddgr-offline-policy-reliability-v03','distinct_contracts','Privacy/inclusion scope and offline/freshness precedence differ. Both expose competing requirements, but neither answer supplies the other policy.'),
 ('mail-fast-reliability-v03','posting-latency-reliability-v03','shared_principle_cross_split','Both operationalize vague performance language into measurable limits. Posting additionally distinguishes UI acknowledgement from remote completion. Treat as transfer of a taught latency-clarification principle, not an entirely unseen reasoning family.'),
 ('mock-away-classifier-reliability-v03','mock-all-network-reliability-v03','shared_principle_cross_split','Both reject replacing tested behavior with a mock and demand real selected logic. The holdout adds adapter/parser composition, but reuses the central no-mocked-away-core principle.'),
 ('missing-integration-reliability-v03','mock-all-network-reliability-v03','shared_principle_cross_split','Both reject a whole-app success claim based on isolated/mocked unit success and require a real composed path. The different app/wiring failure tests domain transfer, not a novel integrity rule.'),
 ('posting-session-undo-redo-external-v02','posting-session-history-limit-external-v02','related_distinct_task','Both use SessionVariables, but one checks edit/revert/redo transitions and branching while the other checks the 50-edit bound and script-value/type preservation.'),
 ('tldr-python-client-cache-freshness-external-v02','tldr-python-client-cache-network-routing-external-v02','related_distinct_task','Freshness computes an age predicate with controlled time; routing uses that collaborator to choose cache/network/fallback. Shared component family is intentional and stays in train.')
]


def main(profile='dataset-profile-v01'):
    paths=active_paths();out=inside(profile)
    originals={r['record_id']:r for p in (paths['tests'],paths['planning'],paths['reliability']) for r in rows(p)}
    metrics={r['record_id']:r for r in rows(out/'records.jsonl')}
    scores={frozenset((p['left'],p['right'])):p['score'] for p in read_json(out/'all-pair-similarities.json')}
    reviews=[]
    for left,right,decision,reason in PAIRS:
        a,b=originals[left],originals[right]
        reviews.append(dict(left=left,right=right,decision=decision,reason=reason,
                            left_split=a['candidate_split'],right_split=b['candidate_split'],cross_split=a['candidate_split']!=b['candidate_split'],
                            score=scores[frozenset((left,right))],
                            evidence={'left_purpose':metrics[left]['purpose'],'right_purpose':metrics[right]['purpose']},
                            record_sha256={r['record_id']:sha256(json.dumps(r,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for r in (a,b)},
                            reviewer='Assistant in this workspace, not an independent external judge.'))
    # Exhaustive exact checks do not replace the targeted semantic adjudications above.
    conversations={};test_asts={};test_bodies={}
    for row in originals.values():
        key=sha256(json.dumps(row['messages'][1:],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        conversations.setdefault(key,[]).append(row['record_id'])
    for row in metrics.values():
        if row['track']!='tests':continue
        test_asts.setdefault(row['complexity']['exact_ast_sha256'],[]).append(row['record_id'])
        for function in row['complexity']['test_body_hashes']:
            test_bodies.setdefault(function['sha256'],[]).append([row['record_id'],function['name']])
    result=dict(status='targeted semantic review completed with cross-split taught-principle overlaps identified; no automatic data removal',
        exact_conversation_duplicates=[v for v in conversations.values() if len(v)>1],
        exact_test_artifact_duplicates=[v for v in test_asts.values() if len(v)>1],
        exact_test_function_body_duplicates=[v for v in test_bodies.values() if len(v)>1],
        pair_adjudications=reviews,scope={'pairwise_retrieval':4485,'cross_split_pairs':1398,'semantic_pairs_adjudicated':len(reviews),
          'embedding_model_used':False,'all_pairs_manually_reviewed':False},
        conclusion='No copied row or identical test artifact/function was found. Four planning variants have substantial expected overlap. Three cross-split principle-overlap pairs make some decision evaluation items policy-transfer checks, not unseen-rule checks. Low lexical similarity alone does not establish semantic independence.',
        recommendation='Keep source-family separation. Before freezing scoring, label decision evaluation as taught-rule transfer or replace/expand the overlapping evaluation scenarios if unseen-problem-family generalization is required. Downweight or separate focused plan variants when comparing independent-app exposure.',
        readiness='Review produces evidence and cautions, not a blanket proof of independent holdout reasoning or model generalization. No split or training selection changed.')
    (out/'semantic-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Semantic pair adjudications:',len(reviews),'; cross-split taught-principle overlaps:',sum(r['decision']=='shared_principle_cross_split' for r in reviews))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',default='dataset-profile-v01')
    main(parser.parse_args().profile)
