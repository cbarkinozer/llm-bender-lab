import json,random
from pathlib import Path
EVENTS={"collected":[],"calls":[],"failures":[]}
def pytest_configure(config):
    import codelang_detect.detector as m
    original=m.detect
    cached=m.PATTERNS
    def broken(text):
        current=m.PATTERNS
        try:
            m.PATTERNS=cached;return original(text)
        finally:m.PATTERNS=current
    m.detect=broken
    import codelang_detect as package
    package.detect=m.detect
def pytest_collection_modifyitems(items):
    EVENTS["collected"]=[item.nodeid for item in items]
def pytest_runtest_logreport(report):
    if report.when=="call":EVENTS["calls"].append(report.nodeid)
    if report.failed:EVENTS["failures"].append({"nodeid":report.nodeid,"when":report.when,"detail":report.longreprtext})
def pytest_sessionfinish(session,exitstatus):
    Path('C:\\Users\\barkin\\Documents\\GitHub\\llm-bender-lab\\experiments\\unit-test-generation\\qwen3.5-4b\\exp-002-task-test-sft\\pilot-v01\\evidence\\20261031T091826454544Z\\language-rules\\cache-initial-configuration\\events.json').write_text(json.dumps(EVENTS),encoding="utf-8")
