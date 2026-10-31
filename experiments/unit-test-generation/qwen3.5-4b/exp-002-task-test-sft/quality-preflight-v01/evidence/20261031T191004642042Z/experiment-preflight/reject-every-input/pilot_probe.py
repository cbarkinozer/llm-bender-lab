import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    import experiment_workflow as m
    def reject(*args,**kwargs):
        raise ValueError("invalid preflight")
    m.run_experiment=reject
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\quality-preflight-v01\\evidence\\20261031T191004642042Z\\experiment-preflight\\reject-every-input\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
