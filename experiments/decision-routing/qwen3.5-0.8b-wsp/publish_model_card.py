"""Publish the reviewed WSP documentation and the separately staged experimental adapter; never upload tokens."""
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd

root = Path(__file__).resolve().parent
api = HfApi()
api.whoami()  # Requires an authenticated account with repository write access.
parent = (root / "preflight/model-card-parent-revision.txt").read_text().strip()
files = {
    "README.md": root / "model-card-updated.md",
    "experiments/wsp/RESULTS.md": root / "RESULTS.md",
    "experiments/wsp/candidate-training-manifest.json": root / "preflight/candidate-training-manifest.json",
    "experiments/wsp/routing-cohort-manifest.json": root / "preflight/routing-cohort-manifest.json",
    "experiments/wsp/training-view-manifest.json": root / "preflight/training-view-manifest.json",
}
result = api.create_commit(
    repo_id="cbarkinozer/Reflex-1",
    parent_commit=parent,
    commit_message="Document WSP base substitution experiment and routing results",
    operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(path))
                for name, path in files.items()] + [
        CommitOperationAdd(path_in_repo="experimental/wsp/adapter/" + p.name, path_or_fileobj=str(p))
        for p in (root.parents[2] / "artifacts/reflex-wsp-routing-completed-20261120/publish-adapter").iterdir() if p.is_file()
    ],
)
print(result.commit_url)
