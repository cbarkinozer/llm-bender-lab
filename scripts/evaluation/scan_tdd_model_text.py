"""Find construction/reviewer context in model-visible messages, not provenance."""
import argparse
import json
from pathlib import Path
import re

TERMS=re.compile(r'\bpaper\b|\breferences?\b|\bstep4\w*\b|llm-bender|\breview(?:er)?\b|\bOccam\b',re.I)
META=re.compile(r'assistant-authored|assistant-proposed|historical (?:user|human) answers|dataset-construction|annotation (?:feedback|status)|absent from model input|checked against test AST|reference uses local image|not (?:a path|facts?) (?:inferred|recoverable)',re.I)


def scan_record(row):
    findings=[]
    for message in row['messages']:
        for part in ('content','reasoning_content'):
            for number,line in enumerate(message.get(part,'').splitlines(),1):
                for match in META.finditer(line):
                    findings.append(dict(role=message['role'],part=part,line=number,term=match.group(),text=line,status='block',reason='Dataset/reviewer construction commentary'))
                for match in TERMS.finditer(line):
                    # This is an actual email citation requirement, not a reference implementation.
                    legitimate=(match.group().lower()=='references' and 'retain references to their source messages' in line)
                    findings.append(dict(role=message['role'],part=part,line=number,term=match.group(),text=line,
                        status='allowed' if legitimate else 'assess',reason='Functional email citation requirement' if legitimate else 'Inspect for repo/history/reviewer context; keyword alone is not proof of leakage'))
    return findings


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('records',type=Path);args=parser.parse_args()
    rows=[json.loads(l) for l in args.records.read_text().splitlines()]
    report={r['record_id']:scan_record(r) for r in rows}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if any(f['status']!='allowed' for findings in report.values() for f in findings):raise SystemExit(1)

if __name__=='__main__':main()
