import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    import codelang_detect.cli as m
    import sys
    from pathlib import Path
    original=m.main
    def broken():
        if len(sys.argv)==2 and Path(sys.argv[1]).is_file():print(Path(sys.argv[1]).suffix.lstrip("."));return
        return original()
    m.main=broken
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v01\\evidence\\20261031T091826454544Z\\language-cli-success\\guess-file-suffix\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
