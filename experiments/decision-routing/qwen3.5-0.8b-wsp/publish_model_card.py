"""Publish the reviewed WSP documentation only; never upload weights or tokens."""
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
                for name, path in files.items()],
)
print(result.commit_url)
