# Initialization ablation: measured diagnostics

Same frozen prompts and primary decoding settings verified across all four arms. SFT step60 uses the same100-step cosine horizon. Development data were already examined; this is not a fresh final test.

| Arm | Dev EOS | Dev median tokens | CETVEL EOS | Grammar subset |
|---|---:|---:|---:|---:|
| base | 20/20 | 205.5 | 100/100 | 71.750% |
| cpt | 8/20 | 4096 | 26/100 | 86.938% |
| base_sft | 20/20 | 42.5 | 100/100 | 71.938% |
| cpt_sft | 20/20 | 24.5 | 100/100 | 86.625% |

Grammar is strict sentence-likelihood recognition on the pinned1600-pair subset, not a writing-quality score. CETVEL task metrics remain separate in the JSON report. Reasoning probes remain separate from primary thinking-disabled comparison. Review the raw answers before choosing an initialization; these automatic metrics do not grade answer correctness or Turkish naturalness.

Owner review completed: all20 valid rankings. CPT-initialized exp007 step60 remains preferred over direct-base exp009 step60:12 wins,3 losses,5 ties. See BASE-SFT160-OWNER-REVIEW.md and its JSON for all verbatim reasoning, pairwise outcomes and limitations. This is a development result, not production readiness.
