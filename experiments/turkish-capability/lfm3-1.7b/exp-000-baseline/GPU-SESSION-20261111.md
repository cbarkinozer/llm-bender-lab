# GPU session 2026-11-11

Owner authorized baseline -> W&B -> Wikipedia LoRA-CPT -> matched evaluation -> verified local recovery. RTX4090 24GB, driver580.126.09, Python3.12.3. Never dispose pod before recovery verification.

W&B enabled for GPU training and evaluation, superseding previous OFF notes. Project lfm3-turkish-post-training; group lfm3-1.7b-turkish-wikipedia-cpt-v01. Secrets stay outside source/artifacts.

Candidate vLLM0.33.0 isolated from training environment, tested before full benchmark. Same sequential native-template BF16 engine, EOS124900, greedy/rep1.05, 4096 output/8192 context; exact-loop and180s cooperative guards before/after. CPT adapter merged into original checkpoint for vLLM; raw likelihood/grammar retain Transformers implementation before/after.

Observed setup issues preserved: premature extraction while SCP incomplete failed; subsequent complete archive SHA matched and re-extraction succeeded. Pip resolver rejected PyArrow23 with datasets5.1.0; changed to24.0.0 and installed via uv. Full transitive freeze required after install. No benchmark outputs were produced by these failures.

Original bundle SHA07fa551afc74d70bb0116b9ea97ffc71ee5c571ed1193394083b448c41294f0c. Runtime source changes are archived separately and final recovery package includes actual executed versions. Working tree uncommitted; preserve source snapshot, commit and diff.

Backend compatibility correction before benchmark: vLLM0.33.0 registry lacks Lfm3ForCausalLM. SGLang PR46858 was open/unmerged. Official vLLM nightly pinned commit7cc0a8a2b1ef6888b44973933c8a208e91122229 selected, runtime validation pending. Isolated environment installs release dependencies then official nightly wheel, followed by pip check. No full benchmark ran with0.33.0. Model download moved from slow single-stream urllib to Hub2.4.0/Xet; pinned checkpoint SHA checks passed. Partial initial transfer retained as setup evidence until recovery.
