import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    from mail_workflow import MailApp
    MailApp.check_idle=lambda self:None
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v02\\evidence\\20261031T094254939039Z\\mail-model-lifecycle\\never-unload-idle-model\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
