# Token and length distributions (native LFM3 template, local tokenizer, no truncation at 4096)

Tokenizer: `experiments/turkish-capability/lfm3-1.7b/base-sft160-runtime-local/tokenizer/tokenizer.json` (sha256 `41927bd314d17d7d...`). Renderer verified: 160/160 rows byte-exact text and token IDs.
Supervised policy: assistant turn incl. <think>..</think>, end-of-turn id 124900 and trailing newline (matches pilot160 recipe). Truncated rows: 0; zero-supervised rows: 0.

Supervised tokens per direction: {'tr-tr': 46088, 'en-tr': 46088, 'tr-en': 35010, 'en-en': 35010} (all: 162196). pilot160 historical: 46088.

## By direction: Supervised (target) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en | 160 | 163 | 464 | 508 | 1015 | 1452 | 35010 |
| en-tr | 160 | 201 | 627 | 729 | 1343 | 2102 | 46088 |
| tr-en | 160 | 163 | 464 | 508 | 1015 | 1452 | 35010 |
| tr-tr | 160 | 201 | 627 | 729 | 1343 | 2102 | 46088 |

## By direction: Total sequence tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en | 160 | 285 | 588 | 664 | 1151 | 1590 | 52513 |
| en-tr | 160 | 315 | 728 | 844 | 1479 | 2240 | 63519 |
| tr-en | 160 | 336 | 641 | 728 | 1243 | 1648 | 60689 |
| tr-tr | 160 | 365 | 795 | 905 | 1570 | 2297 | 71475 |

## By direction: Context (masked) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en | 160 | 99 | 157 | 178 | 240 | 241 | 17503 |
| en-tr | 160 | 99 | 157 | 178 | 240 | 241 | 17431 |
| tr-en | 160 | 145 | 221 | 247 | 336 | 359 | 25679 |
| tr-tr | 160 | 144 | 220 | 246 | 335 | 358 | 25387 |

## By reasoning presence: Supervised (target) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| direct_answer | 520 | 132 | 491 | 579 | 834 | 1343 | 110336 |
| reasoning | 120 | 364 | 695 | 797 | 2102 | 2102 | 51860 |

## By reasoning presence: Total sequence tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| direct_answer | 520 | 275 | 618 | 699 | 948 | 1570 | 175382 |
| reasoning | 120 | 560 | 876 | 1037 | 2240 | 2297 | 72814 |

## By reasoning presence: Context (masked) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| direct_answer | 520 | 118 | 180 | 208 | 299 | 359 | 65046 |
| reasoning | 120 | 161 | 239 | 253 | 335 | 336 | 20954 |

## By direction x reasoning: Supervised (target) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en|direct | 130 | 112 | 416 | 469 | 555 | 1015 | 23582 |
| en-en|reasoning | 30 | 364 | 569 | 683 | 1452 | 1452 | 11428 |
| en-tr|direct | 130 | 144 | 573 | 674 | 834 | 1343 | 31586 |
| en-tr|reasoning | 30 | 402 | 729 | 896 | 2102 | 2102 | 14502 |
| tr-en|direct | 130 | 112 | 416 | 469 | 555 | 1015 | 23582 |
| tr-en|reasoning | 30 | 364 | 569 | 683 | 1452 | 1452 | 11428 |
| tr-tr|direct | 130 | 144 | 573 | 674 | 834 | 1343 | 31586 |
| tr-tr|reasoning | 30 | 402 | 729 | 896 | 2102 | 2102 | 14502 |

## By direction x reasoning: Total sequence tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en|direct | 130 | 229 | 508 | 579 | 640 | 1151 | 36750 |
| en-en|reasoning | 30 | 476 | 736 | 810 | 1590 | 1590 | 15763 |
| en-tr|direct | 130 | 263 | 656 | 785 | 919 | 1479 | 44682 |
| en-tr|reasoning | 30 | 511 | 866 | 1038 | 2240 | 2240 | 18837 |
| tr-en|direct | 130 | 280 | 559 | 624 | 693 | 1243 | 43104 |
| tr-en|reasoning | 30 | 533 | 781 | 905 | 1648 | 1648 | 17585 |
| tr-tr|direct | 130 | 310 | 706 | 829 | 971 | 1570 | 50846 |
| tr-tr|reasoning | 30 | 588 | 932 | 1132 | 2297 | 2297 | 20629 |

## By direction x reasoning: Context (masked) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| en-en|direct | 130 | 94 | 132 | 157 | 219 | 240 | 13168 |
| en-en|reasoning | 30 | 147 | 180 | 226 | 241 | 241 | 4335 |
| en-tr|direct | 130 | 93 | 132 | 157 | 219 | 240 | 13096 |
| en-tr|reasoning | 30 | 147 | 180 | 226 | 241 | 241 | 4335 |
| tr-en|direct | 130 | 140 | 197 | 225 | 320 | 359 | 19522 |
| tr-en|reasoning | 30 | 200 | 253 | 284 | 336 | 336 | 6157 |
| tr-tr|direct | 130 | 139 | 196 | 224 | 319 | 358 | 19260 |
| tr-tr|reasoning | 30 | 199 | 252 | 283 | 335 | 335 | 6127 |

## By category: Supervised (target) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| arithmetic_and_constraints | 116 | 168 | 445 | 507 | 627 | 627 | 22590 |
| assistant_identity | 16 | 53 | 307 | 307 | 307 | 307 | 1576 |
| authorization_and_privacy | 4 | 84 | 126 | 126 | 126 | 126 | 420 |
| clarification_and_uncertainty | 44 | 78 | 241 | 629 | 725 | 725 | 6138 |
| conceptual_explanation | 60 | 489 | 834 | 1015 | 1343 | 1343 | 31662 |
| grammar_and_morphology | 52 | 135 | 249 | 274 | 321 | 321 | 6692 |
| grounded_comprehension | 24 | 46 | 305 | 417 | 417 | 417 | 2712 |
| legal_explanation | 32 | 464 | 605 | 651 | 651 | 651 | 15472 |
| logic_and_critical_reasoning | 52 | 364 | 674 | 676 | 729 | 729 | 16762 |
| planning_and_advice | 124 | 294 | 498 | 546 | 2102 | 2102 | 42254 |
| rewriting_and_summary | 56 | 77 | 145 | 163 | 166 | 166 | 4606 |
| structured_extraction | 44 | 35 | 98 | 141 | 201 | 201 | 2042 |
| technical_method_and_analysis | 16 | 508 | 827 | 827 | 827 | 827 | 9270 |

## By category: Total sequence tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| arithmetic_and_constraints | 116 | 307 | 606 | 728 | 813 | 847 | 40527 |
| assistant_identity | 16 | 158 | 409 | 458 | 458 | 458 | 3288 |
| authorization_and_privacy | 4 | 194 | 235 | 235 | 235 | 235 | 781 |
| clarification_and_uncertainty | 44 | 174 | 351 | 781 | 876 | 876 | 10597 |
| conceptual_explanation | 60 | 611 | 1037 | 1151 | 1570 | 1570 | 39687 |
| grammar_and_morphology | 52 | 224 | 392 | 442 | 484 | 484 | 13067 |
| grounded_comprehension | 24 | 237 | 573 | 597 | 684 | 684 | 6978 |
| legal_explanation | 32 | 575 | 714 | 761 | 773 | 773 | 18824 |
| logic_and_critical_reasoning | 52 | 535 | 799 | 877 | 932 | 932 | 25399 |
| planning_and_advice | 124 | 423 | 626 | 707 | 2240 | 2297 | 56923 |
| rewriting_and_summary | 56 | 221 | 316 | 365 | 451 | 451 | 13172 |
| structured_extraction | 44 | 167 | 287 | 316 | 346 | 346 | 8113 |
| technical_method_and_analysis | 16 | 631 | 903 | 948 | 948 | 948 | 10840 |

## By category: Context (masked) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| arithmetic_and_constraints | 116 | 148 | 220 | 238 | 283 | 284 | 17937 |
| assistant_identity | 16 | 102 | 151 | 152 | 152 | 152 | 1712 |
| authorization_and_privacy | 4 | 71 | 110 | 110 | 110 | 110 | 361 |
| clarification_and_uncertainty | 44 | 101 | 138 | 146 | 152 | 152 | 4459 |
| conceptual_explanation | 60 | 118 | 223 | 241 | 336 | 336 | 8025 |
| grammar_and_morphology | 52 | 121 | 168 | 175 | 200 | 200 | 6375 |
| grounded_comprehension | 24 | 180 | 268 | 299 | 300 | 300 | 4266 |
| legal_explanation | 32 | 104 | 152 | 156 | 157 | 157 | 3352 |
| logic_and_critical_reasoning | 52 | 148 | 246 | 281 | 359 | 359 | 8637 |
| planning_and_advice | 124 | 116 | 153 | 179 | 220 | 221 | 14669 |
| rewriting_and_summary | 56 | 144 | 220 | 235 | 320 | 320 | 8566 |
| structured_extraction | 44 | 137 | 189 | 197 | 219 | 219 | 6071 |
| technical_method_and_analysis | 16 | 83 | 126 | 127 | 127 | 127 | 1570 |

## By source: Supervised (target) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| atlas | 160 | 141 | 341 | 417 | 532 | 532 | 27142 |
| cot | 160 | 251 | 629 | 725 | 2102 | 2102 | 56508 |
| occam | 160 | 41 | 141 | 182 | 474 | 474 | 10204 |
| sft | 160 | 405 | 681 | 827 | 1343 | 1343 | 68342 |

## By source: Total sequence tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| atlas | 160 | 289 | 485 | 573 | 684 | 707 | 50262 |
| cot | 160 | 473 | 832 | 905 | 2240 | 2297 | 83940 |
| occam | 160 | 157 | 270 | 302 | 559 | 606 | 28288 |
| sft | 160 | 513 | 785 | 919 | 1479 | 1570 | 85706 |

## By source: Context (masked) tokens

| Group | rows | median | p90 | p95 | p99 | max | total |
|---|---|---|---|---|---|---|---|
| atlas | 160 | 139 | 208 | 220 | 319 | 320 | 23120 |
| cot | 160 | 161 | 239 | 253 | 358 | 359 | 27432 |
| occam | 160 | 111 | 146 | 162 | 189 | 190 | 18084 |
| sft | 160 | 105 | 145 | 154 | 234 | 235 | 17364 |
