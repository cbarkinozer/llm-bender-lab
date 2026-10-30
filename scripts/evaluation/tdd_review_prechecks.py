"""Presentation and identifier checks shared by the dataset/review tools."""
from html import escape, unescape
import re

META_DEFECT = 'Review/meta text leaked into input or target'


def render_test_field(source):
    """Escape only the review presentation; never transform training messages."""
    rendered = escape(source, quote=False)
    assert unescape(rendered) == source
    return rendered


def check_test_numbering(registry):
    problems = []
    for test in registry:
        name = test['id'].split('::')[-1]
        match = re.match(r'test_r(\d+)_', name)
        if match and 'R'+match.group(1) not in test['requirements']:
            problems.append(dict(test_id=test['id'],numbered_requirement='R'+match.group(1),mapped_requirements=test['requirements']))
    return problems
