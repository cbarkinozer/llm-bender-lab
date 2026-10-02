# Prompt selection v1: manual audit

2026-10-02, project-agent curation. This is not human answer approval.

The agent inspected candidate prompts from the original reviewed-v3 corpus,
exp-006 targeted/repair groups, and all 100 corrected exp-008 prompts. Selection
favored distinct task boundaries and readable inputs over consecutive sampling.
All 100 selected prompts were then read in full, with the final replacement read
separately. Existing answers were not used as new targets or copied to outputs.

## Resolutions before freezing

- A candidate favourite-colour prompt matched an older project benchmark at 0.80
  lexical similarity. Removed it, rather than retaining a rephrased preference
  question. Final `me-081` uses historical `gen-074`: the user's rewritten draft
  and whether the assistant invents regret. Final benchmark lexical flags: zero.
- The provisional label `one_character_contrast` for management/method was too
  narrow. Final `me-072` is `near_word_contrast`; character resemblance does not
  define the number of edits. `me-079` includes the tax/data near-word distinction.
- Within-training pair `me-042` / `me-045` was flagged at 0.6734 similarity.
  Photo-archive planning and explaining learned material use a shared two-week
  planning phrase but different underlying tasks. Both remain train. This is a
  repeated instruction frame, not cross-split leakage; it is not hidden as unique syntax.
- `me-029` / `me-030` conservatively share the product-action scenario group
  because both match similar product names to different actions. Both remain
  validation. There are 100 distinct prompts but 99 declared scenario groups.

## Cross-split semantic review

Reviewed the full train and validation prompt lists and the three closest train
neighbors for each validation prompt (60 ranked pairs in `audit-report.json`).
No selected passage, underlying story, slot-swapped template scenario, or direct
paraphrase was identified on both sides. Representative distinctions:

- Park tense correction and joint-arrival agreement are not train correction
  variants of the same source sentence; shared correction skill is intentional.
- Tower location / slow-tourism definition are not variants of the selected
  train source passages. Source-QA formatting itself is allowed to be shared.
- Validation product-action passages are distinct from train price/time/quantity
  passages; the two conservative product siblings are both held out.
- The mayor's future statement and court ruling do not reuse train summary
  story skeletons with different names or numbers.
- Morning-delay explanation and workspace tradeoffs do not reuse train task
  situations such as meal preparation or photo archiving.
- Presentation scheduling / neighbor-key trust ask about different missing
  variables from training headphone need and job conditions. Shared clarification
  policy is what the dataset is meant to generalize.
- Cafe-sign attribution and unknown retry failure do not duplicate the training
  phone fault, internet intent, elevator cause or meeting-departure scenarios.
- Tax/data rules and connection/dependency passages differ from the selected
  training word contrasts and source statements.
- New-home acknowledgment and a request to listen after an exam do not repeat
  training personal-state prompts or accomplishment situations.
- Expected stock return and a short lateness message do not reuse the training
  contradictory notes, delivery correction or film/bus timing story.

Largest measured cross-split sequence similarity: 0.4675, between the neighbor-key
question and previous-conversation memory question; similar short question
wording, unrelated situations. No cross-split pair exceeded the review thresholds.

This review is fallible and does not establish universal semantic independence.
Future findings require a new prompt version and re-audit. Existing historical
training overlap is deliberately allowed for the new base-start phase. Do not
evaluate prior adapters on these prompts and claim clean unseen performance.

## Not tested or claimed

No answer correctness, final response quality, tokenizer lengths, target masking,
or improvement/forgetting metric has been measured for this new phase. Some
inputs contain intentional grammar errors or synthetic context; source-based
answers must stay bounded to that context. The source manifest's saturation-based
approval history is preserved as a limitation, not relabeled individual human review.
No external CETVEL-wide contamination scan was run for this selection.
