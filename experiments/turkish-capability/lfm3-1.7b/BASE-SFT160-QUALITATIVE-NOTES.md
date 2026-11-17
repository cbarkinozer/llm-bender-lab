# Initialization ablation: qualitative observations

These are agent case inspections of the matched dev20 answers, not owner annotations or an absolute pass-rate estimate. All four arms have raw outputs in the two ignored runtimes. The new four-way Argilla queue has no suggested grades or identities.

The direct-base SFT control does not solve the observed Turkish problems. This means CPT is not a necessary cause of those problems under this small-data recipe. It does not prove CPT is harmless, nor that this160-row dataset or the template is optimal.

| Development item | Direct-base SFT step60 | CPT-SFT step60 | Observation |
|---|---|---|---|
| 01, spelling | Still misses Turkish characters and adds wording | Still misses Turkish characters | Neither reliably corrects spelling |
| 03, sentence merge | Correct natural sentence | Identical correct sentence | Both succeed |
| 09, exact JSON | Echoes instruction into one value; missing required keys | Includes extra label in product value | Both fail exact requested extraction, in different ways |
| 14, ratio |36 litres |33.6 litres | Both wrong; correct larger share is48 litres |
| 16, capacity |6 packages with correct inequality |6 packages, less precise equation/rounding explanation | Direct-base SFT has a good answer here |
| 19, figurative meaning | Interprets a short time interval | Invents an account about visibility of consequences | Neither understands consideration/kindness in context |

Measured findings are stronger for stopping and grammar recognition. CPT raises grammar-subset accuracy from71.75% to86.9375% but reaches the primary output cap on12/20 dev prompts. Both SFT paths stop normally on20/20; direct-base SFT grammar is71.9375%, CPT-SFT86.625%. This supports a CPT stopping regression and a useful grammar-recognition contribution; it does not establish a generation-quality winner.

Next decision should use the four-way responses and task-level evidence, not training loss or the grammar score alone. Keep the existing CPT-SFT winner as the working artifact pending that comparison. Do not discard CPT or expand training merely on the assumption that CPT caused every language error. More epochs on this tiny dataset are not established as a remedy.

[Four-way Argilla review](http://127.0.0.1:6900/dataset/0c2811dd-ee69-488d-83a5-2545f4d4bd9f/annotation-mode):20 prompts, four position-balanced anonymous responses, only ordering and reasoning. Existing reviews remain unchanged. Repeated development examples and recognizable prior answers limit blinding and generalization. No further training or publication was started.
