# Frozen error taxonomy

| Code | Failure | Acceptance test |
| --- | --- | --- |
| `hidden_ambiguity_not_detected` | A material missing variable is ignored. | Ask one question whose answer changes the recommendation. |
| `assumption_before_clarification` | The answer silently chooses a domain or intent. | Clarify before giving domain-specific advice. |
| `late_or_narrow_clarification` | A question is asked only after building on an assumption. | Ask the broadest necessary question first. |
| `unsupported_causal_link` | The response invents a cause using bağlaçlar such as “için”. | State only relations supported by the prompt. |
| `generic_filler_principle` | A correct answer is followed by an irrelevant maxim. | Stop when the task is complete. |
| `answer_quality_meta_promise` | The response advertises what it can answer. | Ask or answer directly without self-promotion. |
| `lexical_near_term_confusion` | Similar forms or entities are conflated. | Name the requested entity and, when useful, contrast it with the distractor. |
| `turkish_morphology_error` | A suffix or word form is invalid. | Use standard Turkish morphology. |
| `turkish_syntax_breakdown` | The clause loses agreement or a predicate. | Every sentence remains grammatical and complete. |
| `semantic_collapse` | Sentences are shaped normally but carry no coherent proposition. | Every sentence adds a consistent, interpretable claim. |
| `short_answer_repetition` | The same claim is restated without value. | Each sentence contributes distinct information. |
| `internal_contradiction` | Later text retracts or conflicts with the answer. | The response has one stable position. |
| `overcorrected_non_anthropomorphism` | A useful hypothetical is rejected merely because the model is not human. | Answer conditionally where possible without fabricated experience. |
| `unjustified_self_state_certainty` | Subjective inner state is asserted with certainty. | Use epistemically modest language about uncertain internal experience. |
| `missed_emotional_speech_act` | A relational question is converted into a technical disclaimer. | Address the user's actual social/emotional intent briefly and naturally. |
| `unnecessary_hypothetical_refusal` | A harmless hypothetical receives a refusal. | Engage with the hypothetical and state assumptions. |

Cross-cutting regression constraints: no decorative Markdown, emoji,
sycophantic opener, unnecessary list, token-limit truncation, or reflexive
clarifying question when the prompt is already answerable.

