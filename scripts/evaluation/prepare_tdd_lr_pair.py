"""Freeze two rationale-supervised learning rates; preserve all earlier artifacts."""
import json
import shutil
from active_tdd_data import EXP, read_json, rows
from prepare_tdd_demo import save, lines, digest

CLARIFICATIONS = {
    'path-parameters': 'Public signatures: extract_path_param_names(url: str) -> list[str]; substitute_path_params(url: str, params: dict[str, str]) -> str. Returned names are bare strings without a colon, unique in first-occurrence order. Placeholder name grammar is [A-Za-z_][A-Za-z0-9_]*. Escaped double-colon tokens are not placeholders. Extraction and substitution operate only on the URL path; substitution also unescapes double colons in that path. Query and fragment are preserved. Behavior on malformed URLs is outside this task.',
    'query-pair-merge': 'Public signatures: extract_query_pairs(url: str, *, escape_dollars: bool = False) -> list[tuple[str, str]]; merge_url_query_into_params(url: str, params: list[tuple[str, str, bool]], *, escape_dollars: bool = False) -> tuple[str, list[tuple[str, str, bool]]]. The merge result is (URL with its query removed, merged triples), preserving the fragment. URL occurrences determine the initial result order; each consumes at most one same-name table occurrence in table order. Unmatched URL pairs become enabled triples; unconsumed table triples follow in their original order. Table enabled flags survive matched occurrences. With no URL pairs, return the unchanged URL and table values. escape_dollars=True makes percent-encoded %24 literal dollar data into doubled dollars before query decoding, for either function. Do not impose behavior for malformed URLs or other percent-encoding spellings.',
    'request-filenames': 'Public signatures: is_valid_filename(filename: str) -> bool; get_unique_request_filename(file_name: str, parent_directory: pathlib.Path) -> str. The proposed result is a basename, not a full path. Supply a basename already ending in .posting.yaml. With no collision the name is unchanged. For an unnumbered input, existing exact .posting.yaml collisions select the first unused two-digit -01, -02, etc. basename. The operation is stateless and creates no files. Native separators mean os.path.sep and os.path.altsep when present on the executing platform; this is not a general Windows-character validator. Reserved device basenames are case-insensitive CON, PRN, AUX, NUL, COM1 through COM9 and LPT1 through LPT9, including an optional single extension. Multi-extension reserved names, other invalid characters, mixed .yml collisions and already-numbered input policy are outside this task.',
    'session-undo-redo': 'Public API: SessionVariables(); .values is a public mutable dict[str, object], not a method; .set(name: str, value: str) -> None; .revert(name: str) -> bool; .undo() -> str | None; .redo() -> str | None. Successful revert is itself an undoable editor edit. Reverting an absent name returns False without altering history or redo. set and successful revert clear redo. Undo and redo restore the affected name\'s previous override presence/value and return that name; an unavailable operation returns None. A removed override means the key is absent, not mapped to an empty string. Do not inspect private history.',
    'session-history-limit': 'Public API: SessionVariables(); .values is a public mutable dict[str, object], not a method; .set(name: str, value: str) -> None; .undo() -> str | None. Scripts write directly through state.values[name] = value. Such writes add no history entry, but a later editor set snapshots that exact prior value including its type. Only the most recent 50 editor edits are retained, not merely 50 current variable keys. Undo those retained edits individually; once exhausted, undo returns None without changing values. Earlier dropped edits cannot be undone. Use public set/undo/values only.'
}


def prepare():
    source=EXP/'paired-preflight-v02/A'; dest=EXP/'lr-pair-preflight-v01'
    if dest.exists(): raise ValueError('Preserve existing preflight')
    requests=rows(source/'development-requests.jsonl')
    for row in requests:
        if row['capability']=='task-to-tests':
            suffix=row['record_id'].removeprefix('posting-').removesuffix('-external-v02')
            row['messages'][-1]['content']+='\n\nFROZEN PUBLIC INTERFACE CLARIFICATION (development revision lr-v01)\n'+CLARIFICATIONS[suffix]
    dest.mkdir()
    for name,rate in [('Exp3',1e-5),('Exp4',3e-5)]:
        folder=dest/name;folder.mkdir()
        for item in source.iterdir():
            if item.is_file() and item.name not in ('manifest.json','recipe.json','development-requests.jsonl','development-encoded.jsonl','prompt-budget.json'):
                shutil.copyfile(item,folder/item.name)
        lines(folder/'development-requests.jsonl',requests)
        recipe=read_json(source/'recipe.json')
        recipe['training']['learning_rate']=rate
        recipe['experiment_id']=name
        recipe['evaluation']['ablation']='Learning rate only within pair; both rationale and answer supervised. Historical A is recipe comparator; revised evaluation requires fresh common base and historical-A inference.'
        recipe['evaluation']['development_revision']='lr-v01: interface declarations clarified after inspecting prior failures; adaptive development, not untouched evaluation. No implementation or reference test code supplied.'
        save(folder/'recipe.json',recipe)
        manifest=read_json(source/'manifest.json')
        manifest['status']='CPU arrays frozen; new runtime/smoke/tiny/reload/baseline gates required'
        manifest['supersedes']='Separate LR-pair preflight; preserves paired-preflight-v02 unchanged'
        manifest['files']={f.name:digest(f) for f in folder.iterdir()}
        save(folder/'manifest.json',manifest)
    save(dest/'protocol.json',dict(arms=['Exp3','Exp4'],loss='rationale-supervised',data_unchanged=True,
        historical_training_comparator='Arm A at 1e-4; old scores not comparable to clarified prompts',
        clarifications=CLARIFICATIONS,primary='Complete reference passing and gated targeted-fault detection',
        checkpoint='Preselected final epoch',holdout='No holdout generation or tuning',
        escape_check='AST-decoded original language-basic strings contain actual newline/tab characters; prior literal-backslash concern was incorrect.'))
    print(json.dumps(dict(output=str(dest),rows=50,supervised_tokens_per_epoch=17266,learning_rates=[1e-5,3e-5])))


if __name__=='__main__':prepare()
