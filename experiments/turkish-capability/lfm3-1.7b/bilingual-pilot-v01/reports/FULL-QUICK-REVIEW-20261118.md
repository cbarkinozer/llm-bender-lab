# Full bilingual quick review — 2026-11-18

Scope: all 160 canonical task groups, Turkish and English prompts, answers and
available reasoning, using revisions/v01-corrections-01/train.jsonl. Cross-direction
alignment checked on all 640 rows. Three parallel read-only review passes covered
g001–g055, g056–g110 and g111–g160. This is a qualitative quick scan, not a complete
external fact-check or a measured dataset error rate. Source problems and
translation problems are distinguished below. No training started. No additional
dataset or Argilla corrections were applied in this scan.

Structural checks: 160 groups, four directions each; zero prompt-body, answer or
reasoning mismatches between corresponding language variants; zero blank answers;
30 original task groups contain separate reasoning. An ignored local API snapshot
and structure-check.json are under crosslingual-runtime-local/bilingual-full-review.
The snapshot found 12 submitted groups with no textbox differences from displayed
originals; this is saved-state evidence only, not a claim about how many the owner
has read. Submitted reviews are not blanket correctness guarantees.

## Main actionable anomalies

| Group | Evidence and concern | Recommended minimal treatment |
|---|---|---|
| g018 | A source describing mutual blame is rewritten as unclear allocation of responsibilities. That supplies a cause not given. | Preserve mutual blame neutrally without inventing responsibility-allocation problems. |
| g022 | Answer rejects deductive validity because premise 4 repeats the conclusion, then says accepting premise 4 yields the conclusion. It also attributes Tanzimat chronology to premises 1–3, which never mention it. | Distinguish valid consequence from independent justification; discuss unsupported generalization in the broader conclusion rather than declaring repetition invalid. Fix reasoning too. |
| g028 | The 1,100 TL cap says total fuel cost, but the answer counts only purchased top-up fuel. | Specify that the cap covers additional purchases. Existing 12.4 L / 535.68 TL solution then fits. |
| g030 | Answer asserts adequate causation and failure ever to use closure/fine powers, although the scenario only gives omitted compliance checking followed by dumping. | Remove invented enforcement history; state liability/causation conditionally. Verify legal provisions separately. |
| g033 | Claims the only new certain consequence is that the named question is not inverted; omits the existential consequence that some question is not inverted. | Include that consequence and avoid claiming an exhaustive finite list of all logical consequences. |
| g035 | Says the employee-hour cap requires every shift to be at most four hours. This only follows under an equal-duration assumption with all six assigned. | Explicitly label equal four-hour shifts as one feasible assumption; unequal durations can also satisfy the cap. |
| g039 | Folding parallel to a midline does not necessarily mean folding along the midline. Reasoning assumes central symmetry. | Specify a fold along the central midline in both language prompts and targets. |
| g063 | Uses a fire without visible smoke to refute “no smoke without fire,” reversing the implication. | Remove this counterexample. Distinguish figurative evidential reliability from literal smoke and things mistaken for smoke. |
| g065 | Blockchain analogy says every participant approves every new transaction; TCP explanation absolutely forbids data before the handshake completes. | Describe acceptance by network consensus rules, not universal unanimity; qualify TCP as the usual simplified exchange. RFC 9293 explicitly permits SYN data (source below). |
| g068 | “taka” / “Takayı” typos. Different species' preferred depths do not guarantee a single-peaked aggregate habitat curve. | Fix takas/Takası. Treat unimodality as a testable assumption rather than a necessary result; keep species-specific objectives. |
| g076 | Turkish asks what the user would realize they could change; English becomes a yes/no “would you realize” question. | Restore the open what-question in both English-input variants. |
| g097 | Three requested bullet points are three unmarked lines; cost risk becomes high cost without supplied magnitude. | Add bullets; retain the supplied risk without intensifying its magnitude. |
| g100 | Summary drops original packaging and refund via original payment method; also omits no-reason entitlement. | Restore operative return/refund conditions concisely. This summarizes supplied text; do not reinterpret it as current legal advice. |
| g104 | Formula combines monetary cost and undefined quality-of-life units, potentially double-counts opportunity cost; cancellation is called a guaranteed Pareto improvement; annual prepayment allegedly reduces loss aversion without support. | Remove formula and guaranteed causal/Pareto claims. Keep verified 600 TL/month, 1,500 TL allowance and 7,200 TL/year arithmetic; compare benefits and alternative uses qualitatively. |
| g105 | Reasoning says local resistance is included among the supplied premises; it is additional historical context. | Separate external context from premises in reasoning and answer. Historical details still need independent source verification if retained. |
| g115 | All three stages are called completed although data collection only started; established theory and begun fieldwork are added. | Preserve completed review, approved methodology and started collection without invented milestones. Prompt's prose/three-items wording can be satisfied with three enumerated sentences in one paragraph. |
| g117 | Shortening preserves shipping eligibility but loses the explicit restriction that only quality-approved pieces may be packed. | Say only approved pieces are packed and shipped; failed pieces are remade. |
| g121 | Adds high-precision sensors, annual timeframe, total operational-energy denominator and a completed calculation. | Frame as proposals and retain unspecified 12% savings potential without invented scope/provenance. Motion sensing is a possible proposal, not established source data. |
| g140 | Source gives 40% very satisfied, question asks all satisfied, answer says 800. | Ask how many were very satisfied, or say total satisfied cannot be determined (at least 800). |
| g142 | Answer and reasoning treat replying “I did not listen” as proof of listening, ignoring hearing/noticing versus attending to content. | Reject necessary self-refutation; explain only possible pragmatic tension. Do not assume the question's premise is true. |
| g144 | Reasoning calls intention causing both time and purchase “reverse direction”; this is a common cause. Also claims extending time cannot increase sales. | Distinguish confounding and reverse causation; say correlation does not establish that extending time would increase sales. |
| g145 | Rewrite introduces team action, email-update promises and always-available support absent from the input. | Remove unsupported operational commitments or mark them as optional text requiring confirmation. |
| g148 | Unspecified 60% attribution becomes 60% of fires; human causes and climate effects are declared necessarily contradictory. | Preserve attribution without inventing its denominator; describe different emphases, noting insufficient information to establish incompatibility. |
| g154 | Requests correctly documented poem examples but supplies titles/attributions without bibliographic details. | Add verified bibliographic references, or narrow the task to correctly attributed titles. Do not delete a poem merely because it has not yet been verified. |

## Separate verification / secondary cleanup queue

- **g012:** “ki” punctuation explanation is overly categorical; obtain authoritative
  orthography guidance before replacing one absolute rule with another.
- **g034:** Keep the exercise's stipulated Turkish classification explicit; do not
  present the translated “because” example as a universal English grammar rule.
- **g071:** Candidate film-title correction: “Karagöz Hacivat Neden Öldürüldü?”
  to “Hacivat Karagöz Neden Öldürüldü?”. A reviewer identified the IKSV film
  catalogue, but parent retrieval failed because of PDF size; verify before applying.
- **g106:** Net pay “30–40% below gross” is an unverified generalization. Remove
  the fixed percentage or establish jurisdiction, date and calculation assumptions.
- **g113:** Missing bullet marker is cosmetic. “Reels is the fastest way” and
  distribution claims are platform-dependent; qualify rather than assert universally.
- **g126:** Candidate update from police 155 to unified emergency 112. Reviewer
  identified official project page; parent retrieval returned HTTP 500. Verify the
  current official source before applying; do not infer that legacy routing fails.
- Existing legal citation flags in **g030, g066, g067, g095, g102, g112, g139,
  g159**, product claims in **g075**, and literary/history claims remain distinct
  source-verification tasks. Unverified is not the same as false. The earlier
  report's proposed edits are not automatically validated by this quick scan.
- **g011** is not a substantive defect merely for restoring Turkish diacritics
  in a column header or naming the supplied time column. **g058** correctly
  preserves a catalog product name. Do not flag legitimate object-language text
  or proper names as failed English translation.

## Previously corrected (not new outstanding findings)

- g081: English comma splice removed.
- g088: supervision and trust changed to supervision and safety.
- g153: final answer now acknowledges inconsistent density conditions.

## Evidence and next action

RFC 9293 §§3.5 and 3.10.7.3 explicitly allow connection synchronization/application
data in SYN segments: https://datatracker.ietf.org/doc/html/rfc9293
This supports qualifying the absolute TCP claim, not replacing the simple lesson
with a long protocol discussion.

Training remains for tomorrow. Before launching, apply the accepted repairs to a
new revision with both-language reasoning/final consistency; preserve immutable
originals and owner edits; refresh validation, token budgets and plan references.
The fresh evaluation remains unchanged. This report does not certify all remaining
factual claims or treat every nonflagged row as owner-approved.
