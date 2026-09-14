# exp-000-benchmark-development

## Goal

Convert, validate, and document the user-provided AdigeBench draft before any
model is evaluated or trained for Adyghe.

## Hypothesis

No model-quality hypothesis is tested here.  This experiment establishes whether
the proposed evaluation artifact is sufficiently specified to support a later
baseline protocol.

## Result

The draft has 200 well-formed sequential TSV rows, but is a candidate only:

- it has nine exact duplicate-input groups, including IDs 011/191, 012/194,
  013/192, 050/193, and 057/195; a tenth repeated question template (159/174)
  has different passage context and remains a distinct input;
- it contains correlated question groups over the same three passages;
- it has 25 morphology/syntax items explicitly marked for native review;
- its source is user-authored and training-authorized; and
- it is derived from `adige data.txt`, so post-training scores represent
  curriculum mastery rather than unseen-data generalization.

See the benchmark README for the protocol and limitations.
