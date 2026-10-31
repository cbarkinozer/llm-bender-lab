import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    from tiny_model import TinyModel
    import torch
    original=TinyModel.load
    def broken(cls,path):
        result=original(path)
        with torch.no_grad():
            for p in result.parameters():p.zero_()
        return result
    TinyModel.load=classmethod(broken)
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v02\\evidence\\20261031T094254939039Z\\tensor-checkpoint-roundtrip\\checkpoint-loses-weights\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
