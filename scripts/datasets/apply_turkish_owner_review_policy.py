"""Apply the owner's prior Occam approval and clarify edited-answer ratings."""
from datetime import datetime, timezone
import json
import os
import argilla as rg
from audit_turkish_sources import ROOT, OUT


def main():
    env=ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            key,sep,value=line.partition('=')
            if sep and key.strip() in ['ARGILLA_API_KEY','ARGILLA_WORKSPACE']:
                os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
    client=rg.Argilla(api_url='http://127.0.0.1:6900',api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    user=next(u for u in client.users if u.username=='argilla')
    workspace=os.getenv('ARGILLA_WORKSPACE','sft-review')
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    receipt={}
    for name in ['turkish-sft-source-calibration-v01','turkish-sft-holdout-test-v01']:
        dataset=client.datasets(name=name,workspace=workspace)
        if dataset is None: raise ValueError('Review dataset missing')
        before={str(r.id):r.to_dict() for r in dataset.records}
        backup=OUT/'review-local'/f'{name}-before-owner-policy-{timestamp}.json'
        backup.write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
        dataset.settings.guidelines=(
            ('HELD-OUT TEST ONLY: references, edits and variants must never enter training. Do not tune or select checkpoints against this set.\n\n' if 'holdout' in name else '')+
            'REVIEW THE FINAL VERSION: Choose keep for a suitable unchanged source answer. Choose edit when you supply a corrected answer; keep the decision as edit even when the result is good. With edit, correctness, instruction following, Turkish quality and amount of detail rate YOUR CORRECTED ANSWER (and corrected prompt if supplied), not the original. With keep, rate the original. Choose reject for unusable items or unsure if unresolved.\n\n'
            'For edit, enter the COMPLETE replacement answer, not a note or partial patch. The original remains visible for provenance. If the prompt needs correction, supply corrected_user too. CoT corrections must contain BOTH the corrected worked solution and final answer, clearly separated. Verify both. Submit explicitly; drafts are not completed review. Good/appropriate ratings alone do not replace missing corrected text.\n\n'
            'OCCAM: The dataset owner has already reviewed the public Occam dataset and confirmed it is good. Untouched selected Occam items are marked keep/pass/pass/good/appropriate under that explicit prior-review instruction; no second review is requested. Existing individual edits/reviews are preserved. Focus new review on the three AlicanKiraz0 sources.\n\n'
            'Content approval and prior owner review are distinct from provenance/leakage checks and training export eligibility. Test assignments remain protected. Repeated system instructions alone are not a reason to reject a record; assess the actual task and intended response.'
        )
        dataset.settings.update()
        updates=[];skipped=[]
        for record in dataset.records:
            if not str(record.id).startswith('occam:'): continue
            if len(record.responses):
                skipped.append(str(record.id));continue
            for question,value in dict(decision='keep',correctness='pass',instruction='pass',turkish='good',detail='appropriate',
                notes='Applied from explicit owner instruction: public Occam dataset previously evaluated and approved by owner; no new item-level review performed by the assistant.').items():
                record.responses.add(rg.Response(question_name=question,value=value,user_id=user.id,status='submitted'))
            updates.append(record)
        if updates: dataset.records.log(updates,batch_size=20)
        after={str(r.id):r.to_dict() for r in dataset.records}
        changed={str(r.id) for r in updates}
        assert set(before)==set(after)
        assert all(after[k]==v for k,v in before.items() if k not in changed), 'Existing reviews changed'
        for key in changed:
            assert after[key]['fields']==before[key]['fields']
            assert after[key]['responses']['decision'][0]['value']=='keep'
        statuses={str(r.id):r.status for r in dataset.records if str(r.id) in changed}
        receipt[name]=dict(occam_prior_approval_applied=len(updates),existing_occam_reviews_preserved=len(skipped),
            existing_other_records_and_responses_unchanged=True,backup=str(backup.relative_to(OUT)),statuses=statuses)
    (OUT/'owner-review-policy-receipt.json').write_text(json.dumps(dict(timestamp_utc=timestamp,datasets=receipt),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
