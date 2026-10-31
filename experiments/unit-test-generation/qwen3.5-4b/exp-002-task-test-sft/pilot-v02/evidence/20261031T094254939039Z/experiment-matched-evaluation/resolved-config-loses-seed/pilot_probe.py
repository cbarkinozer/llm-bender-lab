import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    import experiment_workflow as m
    from pathlib import Path
    import json
    original=m.run_experiment
    def broken(root,name,*a,**k):
        result=original(root,name,*a,**k)
        path=Path(root)/name/'resolved.json'
        data=json.loads(path.read_text());data['seed']=0;path.write_text(json.dumps(data))
        return result
    m.run_experiment=broken
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v02\\evidence\\20261031T094254939039Z\\experiment-matched-evaluation\\resolved-config-loses-seed\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
