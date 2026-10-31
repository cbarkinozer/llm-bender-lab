Review framing B: natural request + visible preparation constraints -> decisions, proposed interface, requirement map, complete pytest files, manual checks, always in that order. Concise rationale is separately reviewable. API names may be proposed in the TARGET; they need not appear in the INPUT. Assistant choices are never historical owner clarifications. Nonessential undecided choices must remain visible.

This is evidence-assisted demo annotation, not blinded scientific review. New backend reference modules do not certify original app UI/CLI wiring. Manual/live integration is pending and explicitly listed. The paper repo and GitHub-insignia are held out from training; review approval cannot change their split.

Option anchors:
Q1 Source relevance: yes = behavior matches source/reference and declared target scope; too-broad = request asks beyond suite/reference; too-narrow = tests require extra behavior absent from request and declared proposals; mismatch = different application behavior; uncertain = source evidence unavailable.
Q2 Interface sufficiency: yes = imports, signatures, schemas and decisions are declared in input OR target agreement; minor-gaps = one or two missing details require guessing; no = undeclared APIs/behavior required; uncertain = cannot inspect evidence. An import inventory alone does not prove method/schema sufficiency.
Q3 Coverage: yes = every important requirement has its core tests or appropriate manual checks; partial-but-disclosed = limitations are explicit and acceptable for this demo; no = a testable requirement is silently missing; uncertain = evidence missing. Do not hide absent backend tests by relabeling them subjective. Live/controller wiring may be checked manually but remains unverified.
Q4a Correctness: all-correct = expected outcomes are correct; some-wrong = at least one wrong expectation; cannot-verify = needed evidence missing.
Q4b Justification: yes = expectations follow from request and explicitly proposed choices; unexplained = values or decisions rely on unstated facts; uncertain = evidence missing. Framing B permits justified design proposals, not pretending names came from the user.
Q5 Assertions: strong = meaningful behavior checks and a killed TARGETED variant for every core requirement; mixed = some coarse oracles or surviving probes; weak = mostly trivial or no useful kills; uncertain = evidence missing. Consult requirement-targeted fault evidence, not equality syntax alone. Kill coverage is not exhaustive bug coverage. A null check is appropriate for a null contract; a documented raises contract can be a strong exception oracle.
Q6 Smells: none = no actionable issue; cosmetic = naming/style only, no fix needed; actionable = harmful coupling, misleading tests, hidden bugs or another concrete teaching defect; uncertain = evidence missing. Related assertions are not automatically poor diagnosis; loops/fixtures/tmp_path do not automatically create smells. Explain concrete harm.
Q8 Rationale: yes = concise, follows the request/declared choices and justifies values; too-long = unnecessary narration; reference-leak = relies on undeclared reference internals; unjustified-values = missing/wrong explanation; uncertain = evidence missing.

Q7 decision rule:
APPROVE only when Q1=yes, Q2=yes, Q3=yes or partial-but-disclosed, Q4a=all-correct, Q4b=yes, Q5=strong or mixed WITH targeted kills for every automated core requirement, Q6=none or cosmetic, Q8=yes, no blocking issues, reference tests pass, three different seeded order runs pass and full sequence <=8192 tokens.
REVISE for fixable violations of that rule. REJECT for mismatch or an unusable/contradictory request requiring rewrite. UNCERTAIN only for missing evidence: name exactly what would resolve it in Blocking issues. An explicit API is necessary but does not excuse an unnecessary private helper dependency.

“Review/meta text leaked into input or target” means dataset construction, revision-history or grading commentary appears in model messages. Legitimate application provenance fields and explicitly chosen public API names are not automatic violations. Preservation requirements need failure-state probes as well as success checks.

Fixed defect categories supplement the lab's contextual smell taxonomy; they do not redefine the paper taxonomy. None of the categories is an automatic verdict without a concrete reason.

Free-text formats (one item per line; enter none in Blocking issues when empty):
Missing interface: name or decision -> where used -> proposed declaration.
Missing coverage: R-id -> missing case -> add test | add manual check | explicitly revise scope.
Assertion/smell evidence: file::test -> fixed category -> reason -> requested fix.
Blocking issues: only approval blockers, or the exact missing evidence for uncertain.
Reviewer confidence: high = inspected enough evidence to apply anchors; low = unresolved uncertainty remains.

Calibration examples (illustrations, not actual submitted ratings):
APPROVE: request requires an integer sum, target declares totals.add(a,b), tests check add(2,3)==5 and add(-2,3)==1, targeted off-by-one variant is killed, stable/ref/token checks pass, rationale explains 5 and 1, no manual gap. All applicable answers yes/all-correct/strong/none; Blocking issues=none.
REVISE: request asks for complete processing but tests only a classifier and import an undeclared internal module; a skipped-assertion case is claimed yet absent. Q1=too-broad,Q2=no,Q3=no,Q4a=cannot-verify,Q4b=unexplained,Q5=mixed,Q6=actionable,Q7=revise. Blocking issues name undeclared API, missing processing tests and false coverage claim. This illustrates the old defect, not a rating of the corrected record.

For this utility demo the owner chose AI review in place of the pending human review. Record reviewer identity and static-versus-executed method explicitly; do not label AI ratings as human agreement. Prior v06 ratings do not approve changed v07 records. No ratings are prefilled. Approval is target review, not a training command or proof of broad generalization.

Historical framing such as new public facade is an editorial assessment flag, not automatic proof of leakage. The v07 portable reference modules validate proposed behavior; original application wiring remains outside the automated checks.
