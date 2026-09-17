# Argilla review UI for exp-001 candidate SFT data

This is a local, human-review UI for the original 2,447 candidate rows in the five
exp-001 pools. It provides a safer editing surface than a CSV editor while
preserving the canonical candidate files unchanged.

## Review contract

For every record, Argilla displays the category rule, user input, and current
candidate target. The `Reviewed target` and optional `Reviewed prompt` fields
are seeded as Argilla suggestions with the existing content.

- If the row is good, accept the suggested target and submit it.
- If it needs a target correction, edit `Reviewed target` directly.
- If the prompt itself is implausible or ambiguous, fill `Reviewed prompt`
  with the corrected full prompt too; otherwise leave it blank.
- `Optional review note` is only for a short reason that will be useful later.

The UI does not assign accept/reject labels. A submitted `Reviewed target` is
the reviewed version of that row. An empty `Reviewed prompt` means the original
prompt carries forward unchanged. Drafts do not count as reviewed.

The candidate CSVs remain the immutable candidate artifact. Exported reviews
are separate, ID-keyed CSVs; a later validation/merge step will create a new
reviewed dataset version only after all required gates pass.

## Start locally on Windows

Docker Desktop must be running. From this folder:

```powershell
.\start_review.ps1
```

It creates an ignored Python virtual environment, starts a localhost-only
Docker stack, imports the five candidate files once, and opens
`http://127.0.0.1:6900`.

For this localhost-only first run, the Docker Compose defaults are:

```text
username: argilla
password: 12345678
API key:  argilla.apikey
workspace: sft-review
```

Before exposing Argilla to another machine, copy `.env.example` to `.env`, set
a strong unique password/API key, and change the port binding deliberately.
Never commit `.env`.

The stack pins Argilla server/client `2.8.0`; client and server stay on the
same version so the review/export contract is explicit and reproducible.

## Daily use

The importer is deliberately non-destructive. Once the dataset exists,
`start_review.ps1` will stop rather than duplicate or overwrite the session.
Just start the services and open the UI:

```powershell
docker compose up --detach
Start-Process http://127.0.0.1:6900
```

When you want a durable review snapshot, export it:

```powershell
$env:ARGILLA_API_URL = "http://127.0.0.1:6900"
$env:ARGILLA_API_KEY = "argilla.apikey"
$env:ARGILLA_WORKSPACE = "sft-review"
.\.venv\Scripts\python.exe export_reviews.py
```

This produces a timestamped CSV under `../../review-exports/` containing only
submitted reviews, including unchanged accepted targets. The script prints an
artifact SHA-256. Do not use `import_candidates.py --replace` until you have
exported the current reviews: replacing intentionally deletes the Argilla UI
dataset and its drafts/submissions.

## Stop or reset

Stop services without deleting reviews:

```powershell
docker compose stop
```

Resume later with `docker compose up --detach`.

To intentionally erase the local Argilla database and all UI review state,
first export it, then run:

```powershell
docker compose down --volumes
```

This does not touch any canonical candidate CSV, but the Argilla reviews are
not recoverable unless exported.
