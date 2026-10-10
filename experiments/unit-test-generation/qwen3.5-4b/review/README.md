# Local test-quality review

Separate Docker Compose project: `bender-unit-test-review`. Argilla 2.8.0 server
is pinned to its ARM64 image digest; dependencies are postgres 14, Redis 7 and
Elasticsearch 8.17.0. All four service images are pinned by digest in the Compose file. Local address: http://127.0.0.1:7900.

Credentials are generated in the ignored `.env` in this directory. Username is
`argilla`; retrieve the password locally from `.env`. Do not commit credentials.
Review data uses separate named volumes from the historical Turkish project.

From repository root:

```sh
docker compose --project-name bender-unit-test-review -f experiments/unit-test-generation/qwen3.5-4b/review/docker-compose.yml up -d
.venv/bin/python experiments/unit-test-generation/qwen3.5-4b/review/create_review.py
```

The schema is development-only, initially empty, and idempotently preserves an
existing dataset. Do not import final holdout into the development workspace.
Human initial ratings should not show model identities or LLM suggestions.
Oracle-site evidence, later judge suggestions, adjudication and edits must remain
separate from original output. Export submitted responses by stable IDs before
changing schema; volume deletion is not part of this workflow.

The dataset was created and a second setup invocation preserved it unchanged.
The server's `/api/v1/status` currently returns a Pydantic serialization error
for Elasticsearch ObjectApiResponse; actual dataset creation/listing works.
Do not treat this endpoint as the readiness gate until that upstream bug is
resolved. This limitation is retained rather than claiming every endpoint passed.
