"""Build an explicit model-only release; upload only with --upload.

Credentials are read in-process from local .env and never written to the payload.
Raw corpora, benchmark examples, optimizer pickles and local logs are excluded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


BASE = 'LiquidAI/LFM3-1.7B'
REVISION = '0dc4268b561499c648c7ba7c9466bf3d8d01517a'
REPO = 'cbarkinozer/LFM3-1.7B-Turkish-CPT'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def credential(root):
    values = {}
    for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.removeprefix('export ').split('=', 1)
            values[key.strip()] = value.strip().strip('\"\'')
    for key in ['HF_TOKEN', 'HF_API_KEY', 'HUGGINGFACE_TOKEN', 'HUGGINGFACEHUB_API_TOKEN']:
        if values.get(key):
            return values[key]
    raise RuntimeError('No Hugging Face credential found in local .env')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--upload', action='store_true')
    args = parser.parse_args()
    from huggingface_hub import HfApi, ModelCard, hf_hub_download
    from safetensors import safe_open
    import numpy as np

    root = Path(__file__).resolve().parents[2]
    track = root/'experiments/turkish-capability/lfm3-1.7b'
    output = track/'preparation-local/hf-release-v01'
    output.mkdir(parents=True, exist_ok=False)
    api = HfApi(token=credential(root))
    identity = api.whoami()
    assert identity['name'] == REPO.split('/')[0], 'Unexpected Hugging Face identity'
    print('Authenticated as '+identity['name'], flush=True)
    upstream = api.model_info(BASE, revision=REVISION)
    for item in upstream.siblings:
        if item.rfilename.upper() in ['LICENSE', 'NOTICE']:
            source = hf_hub_download(BASE, item.rfilename, revision=REVISION, token=api.token)
            shutil.copyfile(source, output/item.rfilename)
    assert (output/'LICENSE').exists()

    names = ['exp-001-wiki-cpt', 'exp-002-mixed-cpt', 'exp-003-cpt-cont-50m', 'exp-004-cpt-cont-100m']
    labels = ['wiki-2m2', 'cpt-10m', 'cpt-50m', 'cpt-100m']
    raw_tokens = [2201862, 9995322, 49995738, 99995385]
    entries = []
    for name, label, raw in zip(names, labels, raw_tokens):
        exp = track/name
        training = exp/'results-local/cpt-v01'
        source = training/'adapter'
        manifest = read(training/'training-manifest.json')
        assert manifest['status'] == 'training_completed' and manifest['training']['epoch'] == 1.0
        config = read(exp/'config-planned.json')
        assert config['model']['repo'] == BASE and config['model']['revision'] == REVISION
        destination = output if label == 'cpt-100m' else output/'checkpoints'/label
        destination.mkdir(parents=True, exist_ok=True)
        weight = source/'adapter_model.safetensors'
        tensor_count = 0
        parameters = 0
        with safe_open(weight, framework='np') as tensors:
            for key in tensors.keys():
                tensor = tensors.get_tensor(key)
                assert tensor.ndim == 2 and np.isfinite(tensor).all(), key
                tensor_count += 1
                parameters += tensor.size
        assert tensor_count > 0
        shutil.copyfile(weight, destination/weight.name)
        adapter = read(source/'adapter_config.json')
        assert adapter['base_model_name_or_path'] == BASE and adapter['r'] == 64
        adapter['revision'] = REVISION
        write(destination/'adapter_config.json', adapter)
        if destination != output:
            (destination/'README.md').write_text(
                f'# {label}\n\nModified by cbarkinozer: Turkish CPT LoRA checkpoint with {raw:,} raw tokens.\n'
                'Load directly on LiquidAI/LFM3-1.7B at revision '+REVISION+'.\n'
                'Do not stack cumulative adapters. See the root model card and LICENSE for results and terms.\n',
                encoding='utf-8')
        entry = dict(label=label, experiment=name, raw_tokens=raw,
            path='.' if destination == output else destination.relative_to(output).as_posix(),
            adapter_sha256=hashlib.sha256(weight.read_bytes()).hexdigest(),
            adapter_tensors=tensor_count, adapter_parameters=parameters,
            full_phase_runtime_seconds=manifest['training']['train_runtime'],
            trainer_token_exposure=manifest['training']['num_tokens'],
            peak_gpu_allocated_bytes=manifest.get('peak_gpu_allocated_bytes'),
            training=config['training'], lineage=manifest.get('lineage'),
            parent_adapter_sha256=manifest.get('parent_adapter_sha256'),
            wandb=read(training/'wandb-run.json'))
        entries.append(entry)
        # Explicit metadata allowlist: no corpus contents or credential-bearing logs.
        meta = output/'reproducibility'/label
        write(meta/'training-summary.json', entry)
        effective = read(training/'effective-training-args.json')
        write(meta/'effective-training-args.json', {k:v for k,v in effective.items()
            if not any(s in k.lower() for s in ['token', 'hub', 'output_dir', 'logging_dir'])})
        requirements = exp/'requirements-gpu.txt'
        if requirements.exists():
            shutil.copyfile(requirements, meta/'requirements-gpu.txt')
        write(meta/'trainer-metrics.json', manifest['training'])
        source_manifest = read(exp/config['active_cpt_manifest'])
        write(meta/'data-provenance.json', {k:source_manifest[k] for k in
            ['source_files','web_revision','source_split','policy','limitations','raw_tokens_no_eos',
             'parent_manifest_sha256','benchmark_sha256','turblimp_sha256','source_manifest_sha256']
            if k in source_manifest})
    assert entries[2]['parent_adapter_sha256'] == entries[1]['adapter_sha256']
    assert entries[3]['parent_adapter_sha256'] == entries[2]['adapter_sha256']
    for name in ['tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja']:
        shutil.copyfile(track/names[-1]/'results-local/cpt-v01/adapter'/name, output/name)
    notice = ('Independent Turkish CPT release by Barkin Ozer / cbarkinozer.\n'
        'Original model: Liquid AI, Inc., LiquidAI/LFM3-1.7B, revision '+REVISION+'.\n'
        'Modified files: adapter_model.safetensors in the root and checkpoint folders contain\n'
        'new Turkish CPT LoRA weights. adapter_config.json files additionally pin the base revision.\n'
        'Release documentation and evaluation summaries were added by cbarkinozer.\n'
        'Tokenizer files are copied unchanged. Upstream license is retained verbatim in LICENSE.\n'
        'No affiliation with or endorsement by Liquid AI is implied.\n')
    notice_path = output/'NOTICE'
    notice_path.write_text((notice_path.read_text(encoding='utf-8')+'\n' if notice_path.exists() else '')+notice, encoding='utf-8')

    screening = read(track/'continuation-screen-results-v01.json')
    earlier = read(track/'cpt-fast100-results-v02.json')
    language = {}
    for name, result in screening['results'].items():
        language[name] = dict(grammar_macro_accuracy=result['grammar']['macro_accuracy'],
            grammar_per_phenomenon=result['grammar'].get('per_phenomenon'),
            text={k:{f:v[f] for f in ['nll','perplexity','scored_tokens','source_sha256']}
                for k,v in result['text']['results'].items()})
    wiki = earlier['results'][names[0]]
    language[names[0]] = dict(grammar_macro_accuracy=wiki['grammar_macro_accuracy'], text=wiki['text'])
    write(output/'evaluation/language-results.json', language)
    public_screen = dict(protocol=screening['protocol'], results={})
    for name, result in screening['results'].items():
        m = result['manifest']
        assert m['status'] == 'completed' and m['count'] == 100
        public_screen['results'][name] = dict(scores=result['scores'],
            answers_sha256=result['answers_sha256'],
            manifest={k:m[k] for k in ['protocol','selected_ids','questions_sha256','count','seed',
                'engine_args','eos_token_ids','chat_template_sha256','decoding','packages','wall_seconds']})
    write(output/'evaluation/matched-screening-100.json', public_screen)
    final = track/names[-1]/'results-local/official-general-500-v01/cetvel'
    fm = read(final/'manifest.json')
    assert fm['status'] == 'completed' and fm['count'] == 500
    fs = read(final/'scores.json')
    write(output/'evaluation/cpt-100m-full500.json', dict(scores=fs,
        answers_sha256=hashlib.sha256((final/'answers.jsonl').read_bytes()).hexdigest(),
        manifest={k:fm[k] for k in ['protocol','selected_ids','questions_sha256','count','seed',
            'engine_args','eos_token_ids','chat_template_sha256','decoding','packages','wall_seconds']}))
    write(output/'reproducibility/checkpoints.json', entries)
    write(output/'reproducibility/release.json', dict(repo=REPO, base_model=BASE, base_revision=REVISION,
        study_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        publication_validation='Finite tensors, shapes, hashes, lineage and result counts checked on CPU; no new full GPU load during publishing.'))
    for runtime in ['training', 'inference']:
        source = track/'preparation-local/gpu-20261112'/(runtime+'-runtime.json')
        captured = read(source)
        write(output/'reproducibility'/(runtime+'-runtime.json'), {k:v for k,v in captured.items()
            if k not in ['executable', 'environment', 'nvidia_smi']})
        freeze = source.with_suffix('.freeze.txt')
        shutil.copyfile(freeze, output/'reproducibility'/freeze.name)

    def table(header, rows):
        return '\n'.join(['| '+' | '.join(header)+' |', '| '+' | '.join(['---']*len(header))+' |']+
            ['| '+' | '.join(map(str,row))+' |' for row in rows])
    order = [('Starting model','exp-000-baseline'),('Wiki 2.2M',names[0]),('10M',names[1]),('50M',names[2]),('100M',names[3])]
    language_table = table(['Checkpoint','Wikipedia NLL ↓','Web NLL ↓','TurBLiMP macro accuracy ↑'],
        [[label,f"{language[name]['text']['wiki_eval']['nll']:.4f}",f"{language[name]['text']['web_eval']['nll']:.4f}",
          f"{100*language[name]['grammar_macro_accuracy']:.2f}%"] for label,name in order])
    generation_rows = []
    for label,name in [order[0]]+order[2:]:
        result = screening['results'][name]['scores']; score = result['results']; t = result['termination']
        generation_rows.append([label,f"{score['tquad']['f1']:.4f}",f"{score['xquad_tr']['f1']:.4f}",
            f"{score['wmt_en_tr']['corpus_chrf']:.2f}",f"{score['mlsum_tr']['mean_rougeL']:.4f}",
            t.get('eos',0),t.get('length',0),t.get('exact_loop',0)])
    generation_table = table(['Checkpoint','TQUAD F1 ↑','XQuAD F1 ↑','Translation chrF ↑','Summary ROUGE-L ↑',
        'EOS /100','Length /100','Loop guard /100'], generation_rows)
    full = fs['results']
    full_table = table(['Measure','100M, 500 questions'],[
        ['TQUAD F1',f"{full['tquad']['f1']:.6f}"],['XQuAD F1',f"{full['xquad_tr']['f1']:.6f}"],
        ['Translation chrF',f"{full['wmt_en_tr']['corpus_chrf']:.4f}"],
        ['Summary ROUGE-L',f"{full['mlsum_tr']['mean_rougeL']:.6f}"],
        ['GECTurk exact match','0.0'],['Normal EOS','136 /500'],['Output limit','340 /500'],['Exact-loop guard','24 /500']])
    training_table = table(['Phase','Added raw tokens','Runtime (minutes)','Trainer token exposure'],
        [[e['label'],f"{added:,}",f"{e['full_phase_runtime_seconds']/60:.2f}",f"{int(e['trainer_token_exposure']):,}"]
         for e,added in zip(entries,[2201862,9995322,40000416,49999647])])
    card = (track/'model-release/README.template.md').read_text(encoding='utf-8')
    for marker,replacement in [('LANGUAGE_RESULTS',language_table),('GENERATION_RESULTS',generation_table),
            ('FULL_RESULTS',full_table),('TRAINING_RESULTS',training_table)]:
        assert '<!-- '+marker+' -->' in card
        card = card.replace('<!-- '+marker+' -->', replacement)
    (output/'README.md').write_text(card, encoding='utf-8')
    (output/'README.md').write_text(card+'\n### Training run records\n\n'+ '\n'.join(
        '- ['+e['label']+']('+e['wandb']['url']+')' for e in entries)+
        '\n\nRun dashboards may require access; the included JSON summaries do not.\n',encoding='utf-8')
    shutil.copyfile(track/'model-release/README.template.md', output/'reproducibility/model-card.template.md')
    code = output/'reproducibility/code'
    code.mkdir(parents=True,exist_ok=True)
    for folder,pattern in [('datasets','*lfm3*.py'),('training','*lfm3*.py'),('evaluation','*lfm3*.py')]:
        for source in (root/'scripts'/folder).glob(pattern):
            destination = code/folder/source.name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,destination)
    shutil.copyfile(root/'scripts/evaluation/score_cetvel_generation.py',code/'evaluation/score_cetvel_generation.py')
    # Each payload file is whitelisted by construction. Scan against actual local
    # credential values without logging their contents or matching source lines.
    secrets = []
    for line in (root/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            value = line.split('=',1)[1].strip().strip('\"\'')
            if len(value) >= 16:
                secrets.append(value.encode())
    files = sorted(p for p in output.rglob('*') if p.is_file())
    for path in files:
        assert path.suffix not in ['.bin','.pt','.pth','.pem','.key'], path.name
        if path.suffix != '.safetensors':
            payload = path.read_bytes()
            assert not any(secret in payload for secret in secrets), 'Credential found in release payload'
    checksums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(output).as_posix()+'\n' for p in files)
    (output/'SHA256SUMS').write_text(checksums,encoding='utf-8')
    ModelCard.load(output/'README.md').validate()
    print('Release validated: '+str(len(files)+1)+' files, '+str(sum(p.stat().st_size for p in files))+' bytes',flush=True)
    if args.upload:
        api.create_repo(REPO,repo_type='model',private=False,exist_ok=True)
        commit = api.upload_folder(repo_id=REPO,folder_path=output,
            commit_message='Release Turkish CPT adapters, checkpoint comparisons and reproducibility metadata')
        remote_files = set(api.list_repo_files(REPO,revision=commit.oid))
        assert {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()} <= remote_files
        remote = {item.rfilename:item for item in api.model_info(REPO,revision=commit.oid,files_metadata=True).siblings}
        for path in output.rglob('*'):
            if not path.is_file():
                continue
            item = remote[path.relative_to(output).as_posix()]
            data = path.read_bytes()
            if item.lfs:
                digest = item.lfs.sha256 if hasattr(item.lfs,'sha256') else item.lfs['sha256']
                assert digest == hashlib.sha256(data).hexdigest(), path.name
            else:
                assert item.blob_id == hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(), path.name
        write(track/'model-release/publication-receipt.json',dict(repo=REPO,url='https://huggingface.co/'+REPO,
            commit=commit.oid,files=len(files)+1,status='published_all_remote_payload_hashes_verified',
            adapter_hashes={e['label']:e['adapter_sha256'] for e in entries}))
        print('Published https://huggingface.co/'+REPO+' at '+commit.oid,flush=True)


if __name__ == '__main__':
    main()
