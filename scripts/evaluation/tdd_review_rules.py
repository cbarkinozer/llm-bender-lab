"""Check review consistency; never create or submit a human approval."""


def approval_blockers(answers, record, blocking_issues):
    """Return violations of the published approval rule, not a quality verdict."""
    allowed={
        'source_relevance':{'yes'}, 'interface_quality':{'yes'},
        'coverage':{'yes','partial-but-disclosed'},
        'expectation_correctness':{'all-correct'}, 'expectation_justification':{'yes'},
        'assertion_quality':{'strong','mixed'}, 'smell_quality':{'none','cosmetic'},
        'reasoning_quality':{'yes'},
    }
    problems=[name+': '+str(answers.get(name,'missing')) for name,values in allowed.items() if answers.get(name) not in values]
    validation=record['validation']
    if not validation['reference_pass']:problems.append('reference suite did not pass')
    if not validation['all_core_requirements_have_killed_variant']:problems.append('core requirement lacks targeted killed variant')
    if not validation['three_order_runs_pass']:problems.append('three shuffled-order runs not passing')
    if not record['tokens']['within_limit']:problems.append('full sequence exceeds token limit')
    if blocking_issues.strip().lower()!='none':problems.append('blocking issues listed or not explicitly cleared')
    if answers.get('confidence') not in ('high','low'):problems.append('reviewer confidence missing')
    return problems


def validate_submitted_decision(answers, record, blocking_issues):
    decision=answers.get('approval')
    if decision=='approve':return approval_blockers(answers,record,blocking_issues)
    if decision=='uncertain' and blocking_issues.strip().lower() in ('','none'):
        return ['uncertain requires the exact missing evidence in Blocking issues']
    if decision in ('revise','reject') and blocking_issues.strip().lower() in ('','none'):
        return ['revise/reject requires concrete blocking issues']
    if decision not in ('approve','revise','reject','uncertain'):return ['overall decision missing']
    return []


def agreement(pairs):
    """Q7 agreement from paired actual ratings, excluding unreviewed records."""
    complete=[(a,b) for a,b in pairs if a is not None and b is not None]
    matches=sum(a==b for a,b in complete)
    return {'agreements':matches,'paired_records':len(complete),
            'rate':matches/len(complete) if complete else None}
