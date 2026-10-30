"""Inspect model-visible text for process words and repo/lab identity leakage."""
import argparse
import json
from pathlib import Path
import re

REPO_NAMES = r'github[-_]insignia|ghost[-_]box|slm[-_]test[-_]generation|llm[-_]bender(?:[-_]lab)?|reflexmodels|codelang[-_]detect|repo[-_]context|cryptocurrency[-_]analyser|miniature[-_]llms'
# Letter boundaries also detect test_revisions.py and model_revision.
TERMS = re.compile(r'(?<![A-Za-z])(?:revisions?|references?|paper|reviews?|reviewer|step4\w*|Occam|'+REPO_NAMES+r')(?![A-Za-z])', re.I)
META = re.compile(r'assistant-authored|assistant-proposed|historical (?:user|human) answers|dataset-construction|annotation (?:feedback|status)|absent from model input|checked against test AST|reference uses local image|not (?:a path|facts?) (?:inferred|recoverable)|/Users/[^/]+/Documents/GitHub/', re.I)
SCHEMA_IDENTIFIERS = {'model_revision','data_revision','code_revision','source_revision','tokenizer_revision'}


def normalized(name):
    return re.sub(r'[-_]', '', name).lower()


def scan_record(row):
    findings = []
    roots = {normalized(i['module'].split('.')[0]) for i in row.get('interface',{}).get('imports',[])}
    for message in row['messages']:
        for part in ('content','reasoning_content'):
            fenced = False
            for number,line in enumerate(message.get(part,'').splitlines(),1):
                if line.lstrip().startswith('```'):fenced = not fenced
                for match in META.finditer(line):
                    findings.append(dict(role=message['role'],part=part,line=number,term=match.group(),text=line,status='block',reason='Dataset/reviewer construction commentary or local source path'))
                for match in TERMS.finditer(line):
                    reason = None
                    identifier = next((m.group() for m in re.finditer(r'[A-Za-z_]\w*',line) if m.start()<=match.start() and m.end()>=match.end()), '')
                    if identifier in SCHEMA_IDENTIFIERS:
                        reason = 'Functional revision/provenance field in the application contract'
                    elif match.group().lower().startswith('revision') and re.search(r'(?:source|model(?:/data)?|data|code|tokenizer|effective)\s+revisions?$',line[:match.end()],re.I):
                        reason = 'Functional source/model/data provenance requirement'
                    elif match.group().lower().startswith('revision') and re.match(r'revisions? identities/seed/settings',line[match.start():],re.I):
                        reason = 'Functional identity/seed/settings manifest contract'
                    elif match.group().lower()=='references' and 'retain references to their source messages' in line:
                        reason = 'Functional email citation requirement'
                    elif normalized(match.group()) in roots and (fenced or line[:match.start()].count('`')%2==1):
                        reason = 'Declared public API identifier, not an undeclared source-repo hint'
                    elif message['role']=='user' and re.fullmatch(REPO_NAMES,match.group(),re.I):
                        reason = 'Product name explicitly supplied in the natural user request'
                    findings.append(dict(role=message['role'],part=part,line=number,term=match.group(),text=line,
                        status='allowed' if reason else 'assess',reason=reason or 'Inspect process/repo context; the keyword alone does not prove leakage'))
    return findings


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('records',type=Path);args=parser.parse_args()
    rows=[json.loads(l) for l in args.records.read_text().splitlines()]
    report={r['record_id']:scan_record(r) for r in rows}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if any(f['status']!='allowed' for findings in report.values() for f in findings):raise SystemExit(1)

if __name__=='__main__':main()
