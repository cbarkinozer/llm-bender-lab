# Complexity-count correction

The initial complexity collector counted some class methods twice because Radon returns methods both within Class blocks and as standalone blocks. The collector now deduplicates by source location and includes nested classes. A regression test verifies methods and closures are counted once.

Use dataset-profile-v02 and original-source-complexity-v02. The v01 source/reference aggregates are superseded; original artifacts remain preserved. Generated test-function CC, token statistics, domains and semantic judgments are unchanged. Original non-test source across the 11 active families has 2412 functions, CC mean 5.44 and population std 7.85. No training examples or model-visible data changed.
