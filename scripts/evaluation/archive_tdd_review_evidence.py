"""Copy fresh execution/fault/order evidence into a portable review bundle."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    evidence=bundle/'evidence'
    def relative(path):return path.relative_to(ROOT).as_posix()
    def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
    def copy_log(source,destination):
        source=Path(source)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        return relative(destination)
    execution=json.loads((bundle/'token-and-execution-report.json').read_text(encoding='utf-8'))
    for run in execution['reports']:
        run['original_log']=run['log']
        run['log']=copy_log(run['log'],evidence/'execution'/(run['repo']+'.log'))
    save(bundle/'token-and-execution-report.json',execution)
    save(evidence/'execution/results.json',execution)
    save(bundle/'execution-receipt.json',dict(results=relative(evidence/'execution/results.json'),passed=all(r['returncode']==0 for r in execution['reports'])))
    for kind in ('fault','stability'):
        receipt_path=bundle/(kind+'-receipt.json')
        receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
        report=json.loads(Path(receipt['results']).read_text(encoding='utf-8'))
        for row in report['results']:
            label=row['fault'] if kind=='fault' else str(row['seed'])
            row['original_log']=row['log']
            original=Path(row['log'])
            row['log']=copy_log(original,evidence/kind/row['repo']/(label+'.log'))
            if kind=='fault':
                plugin=original.parent/'fault_probe.py'
                assert sha256(plugin.read_bytes()).hexdigest()==row['mutation_sha256']
                row['mutation_source']=copy_log(plugin,evidence/kind/row['repo']/(label+'.txt'))
        target=evidence/kind/'results.json'
        save(target,report)
        receipt['original_results']=receipt['results'];receipt['results']=relative(target)
        save(receipt_path,receipt)
    files={p.relative_to(evidence).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(evidence.rglob('*')) if p.is_file() and p.name!='index.json'}
    save(evidence/'index.json',dict(files=files,note='Portable fresh v07 evidence; original execution paths retained as provenance.'))
    print(json.dumps(dict(files=len(files),bytes=sum(p.stat().st_size for p in evidence.rglob('*') if p.is_file()))))


if __name__=='__main__':main()
