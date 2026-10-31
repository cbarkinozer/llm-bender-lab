import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    import reflexmodels.protocol as m
    import json
    original=m.request_to_json
    def broken(*a,**k):
        row=json.loads(original(*a,**k));row['options']={'wrong':'option'};return json.dumps(row)
    m.request_to_json=broken
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v02\\evidence\\20261031T094254939039Z\\decision-requests\\request-loses-original-option-ids\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
