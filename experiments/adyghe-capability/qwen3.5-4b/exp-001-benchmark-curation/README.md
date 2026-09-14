# exp-001-benchmark-curation

## Goal

Create a minimally corrected development revision of the user-provided
AdygheBench draft, without inventing any unverified Adyghe targets.

## Parent

`exp-000-benchmark-development`

## Change

[`AdygheBench v0.2-candidate`](../../../../benchmarks/adigebench/v0.2-candidate/README.md)
has 188 items. It removes 12 source rows: duplicate inputs, one semantically
wrong prompt/reference pair, and two items whose prompt permits incompatible
answers without scenario context.

The original 200-item v0.1 artifact remains unchanged for provenance. This is
a benchmark-revision change, so scores from v0.1 and v0.2 must never be pooled
or compared as though they came from the same test set.

## Status

`candidate`: native review remains required before a model baseline is run or
a result is reported.
