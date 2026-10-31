"""Resolve current data through configuration, without treating old bundles as active."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXP=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'


def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def inside(relative, experiment=EXP):
    target=(experiment/relative).resolve()
    if not target.is_relative_to(experiment.resolve()):raise ValueError('Path escapes experiment')
    return target


def active_paths(experiment=EXP):
    config=read_json(experiment/'config-planned.json')
    index_path=inside(config['active_candidate_index'],experiment)
    index=read_json(index_path)
    return dict(config=config,index=index_path,tests=inside(index['materialized_records'],experiment),
                planning=inside(config['planning_drafts']+'/records.jsonl',experiment),
                reliability=inside(config['reliability_drafts']+'/records.jsonl',experiment),
                baseline=inside(config['baseline_packet'],experiment),
                preview=inside(config['intent_only_preview'],experiment))
