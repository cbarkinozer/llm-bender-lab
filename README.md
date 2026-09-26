# llm-bender-lab

A reproducible lab for fine-tuning and specializing language models for targeted capabilities.

Repository-specific agent instructions live in [AGENTS.md](./AGENTS.md). Operational fine-tuning, dataset, evaluation, experiment, and reproducibility guidance is available under [`docs/`](./docs/).

![LLM Bender Lab](./llm-bender-lab.png)

llm-bender-lab is an experimentation repository for adapting language models to tasks such as Turkish language improvement, tool calling, code generation, structured output, and other specialized capabilities.

Each experiment follows a controlled workflow:

```txt
                       Goal
                        ↓
                     Baseline
                        ↓
                     Dataset
                        ↓
              Training Configuration
                        ↓
           Smoke Test / Tiny Overfit
                        ↓
                    Fine-tuning
                        ↓
                    Evaluation
                        ↓
                Regression Analysis
                        ↓
                    Iteration
```

Models, datasets, training methods, and frameworks may vary by experiment. The focus is on reproducibility: versioned code and data, explicit configs, measurable baselines, and post-training evaluation.

Training code, experiment definitions, evaluation scripts, and result summaries live in this repository. Larger datasets and released adapters can be published on Hugging Face, while training runs and metrics can be tracked with tools such as Weights & Biases.

Specialization may intentionally trade some general capability for stronger performance in a target domain. The important part is to measure and understand that trade-off.

Start with a general model, bend it toward a specific capability, and measure what changed.

## Fine-Tuning Roadmap (TODO)

The breadth-first post-training curriculum, including SFT, preference
optimization, RLVR, reasoning training, CPT/DAPT, distillation, tool use,
cross-lingual transfer, quantization, MoE, VLM, text diffusion, decision models,
and the later depth phase, is maintained in
[`docs/post-training-learning-roadmap.md`](docs/post-training-learning-roadmap.md).
The domain roadmap below provides the original project context; the curriculum
document is the source of truth for the order of future method-learning pilots.

The goal of this project is not to fine-tune models simply for the sake of producing another adapter. Each experiment should answer a concrete question about what fine-tuning can realistically teach a small language model.

The roadmap progresses through four increasingly difficult problems:

1. Improving an already-known language
2. Teaching a tiny model a highly efficient communication policy
3. Adapting a model to a genuinely low-resource language
4. Specializing a model around an agentic software-engineering workflow

The experiments primarily use models from the Qwen3.5 family. `0.8B` is preferred when the target behavior does not require substantial additional model capacity, while `4B` is used when language understanding, reasoning, coding ability, or cross-lingual transfer are likely to become bottlenecks — and, in practice so far, whenever the project is still validating a new dataset/method for the first time, since debugging the method and a weak model simultaneously is avoided. `0.8B` is treated as a later step, attempted once a given behavioral target has already been proven on `4B`.

The intention is to keep the experiments small enough to reproduce locally while still producing meaningful and measurable results.

---

### 1. Turkish Capability Improvement

- **Model:** `Qwen3.5-4B`
- **Primary evaluation:** CETVEL
- **Method:** BF16 LoRA / SFT with Unsloth

The first experiment asks a relatively simple question:

> Can supervised fine-tuning measurably improve the Turkish capability of an already multilingual 4B model?

Rather than evaluating the result subjectively by chatting with the model, the experiment will use **CETVEL** as an external Turkish benchmark.

The base model will first be evaluated on CETVEL to establish a baseline. A Turkish instruction dataset will then be created or assembled independently of the benchmark, followed by BF16 LoRA fine-tuning with Unsloth. QLoRA is intentionally avoided because Unsloth reports higher-than-normal quantization differences for Qwen3.5.

The same CETVEL evaluation will then be repeated under identical inference settings.

The core comparison is therefore:

```text
Qwen3.5-4B
      ↓
CETVEL baseline
      ↓
Turkish training corpus
      ↓
BF16 LoRA / SFT
      ↓
CETVEL evaluation
      ↓
Δ CETVEL
```

The CETVEL evaluation set must remain completely outside the training corpus. Benchmark questions, translated versions of benchmark questions, or obviously derivative examples should not be included in training.

This experiment establishes the basic training and evaluation pipeline that can later be reused for more difficult experiments.

**Outcome (see `experiments/turkish-capability/`):** the baseline diagnostic found no Turkish-fluency gap — the model's raw Turkish is already fluent and grammatically correct. The actual, reproducible weakness is that it won't emit a bare/terse answer under a structured-task prompt (GEC, extractive QA, summarization); it defaults to explaining itself instead of completing the task. That finding turned out to be exactly the "Efficient Tiny Assistant" behavioral-specialization question below, just discovered empirically through Turkish rather than planned from scratch. This experiment line is closed; the follow-up lives in `experiments/response-style-control/` and folds into experiment 3.

#### Main measurements

* CETVEL score before fine-tuning
* CETVEL score after fine-tuning
* Improvement by individual task/category
* Overall average improvement
* Training loss and validation loss
* Training time
* Peak memory usage
* Adapter size
* Inference behavior before and after fine-tuning

A secondary evaluation can test whether improving Turkish significantly damages existing English, reasoning, or coding capability.

The desired result is not merely a lower training loss. The fine-tuned model should demonstrate a measurable improvement on Turkish tasks that were not present in its training data.

---

### 2. Low-Resource Adige Adaptation

- **Model:** `Qwen3.5-4B`
- **Writing system:** Cyrillic
- **Training-data direction:** primarily English → Adige
- **Evaluation:** Adige adaptation of CETVEL + human validation

The second experiment extends the language-adaptation problem into a much more difficult setting:

> Can a multilingual 4B model acquire substantially better capability in a very low-resource language using synthetic cross-lingual training data?

The target language is **Adige**, or Western Circassian.

Unlike Turkish, high-quality Adige instruction datasets are extremely limited. Dataset construction therefore becomes part of the experiment itself.

The model will operate primarily in **Adige Cyrillic rather than Latin transliteration**.

This has several advantages:

* Cyrillic is the standard modern writing system for Adige.
* A larger proportion of naturally occurring Adige text uses Cyrillic.
* Existing dictionaries, educational material, publications, and online resources are more likely to use Cyrillic.
* Adige phonology is represented more consistently in its established Cyrillic orthography than through arbitrary Latin transliterations.
* Avoiding transliteration removes an additional source of normalization errors.

Learning enough Cyrillic to inspect generated examples is therefore preferable to converting the entire language pipeline into Latin characters.

#### Evaluation dataset

An already capable larger LLM can be used to translate or adapt suitable parts of CETVEL into Adige.

The objective is not to claim that a machine-translated CETVEL is automatically a standardized Adige benchmark. Instead, it provides a controlled evaluation set that mirrors the structure of an existing benchmark.

The process can look roughly like:

```text
CETVEL
   ↓
Strong multilingual LLM
   ↓
Adige translation/adaptation
   ↓
Automatic validation
   ↓
Human inspection
   ↓
Adige evaluation set
```

A native speaker, particularly my grandfather, can manually inspect a representative subset of these examples and check:

* semantic correctness,
* grammatical correctness,
* naturalness,
* vocabulary choice,
* whether the translated question preserves the original task,
* whether the expected answer is still valid.

Language-specific Turkish tasks should not necessarily be translated literally. Tasks that depend explicitly on Turkish spelling, morphology, cultural knowledge, or other Turkish-specific phenomena may need to be excluded or replaced with an Adige-appropriate equivalent.

The resulting dataset should therefore be considered an **Adige adaptation inspired by CETVEL**, rather than a blindly translated benchmark.

#### Training corpus

The evaluation benchmark and training corpus must be produced independently.

Training examples will primarily be generated through:

```text
English
   ↓
Strong Adige-capable teacher model
   ↓
Adige
```

English is selected as the primary bridge language because modern foundation models generally possess very strong English representations and because high-quality source material exists for an enormous range of domains.

Russian can still be used as an additional source language where useful, especially when Adige-specific material, dictionaries, educational resources, or parallel text already exist in Russian.

The important separation is:

```text
English / Russian source corpus
            ↓
     Synthetic Adige
            ↓
       TRAINING DATA


CETVEL
   ↓
Adige adaptation
   ↓
EVALUATION DATA
```

These two pipelines must remain isolated to prevent benchmark contamination.

Potential training examples include:

* general instructions,
* question answering,
* everyday conversation,
* factual explanations,
* short stories,
* translation,
* summarization,
* vocabulary,
* grammar examples,
* cultural material,
* multi-turn dialogue.

Synthetic samples should be filtered for obvious translation errors, malformed Cyrillic, duplicated examples, language mixing, and low-quality teacher outputs.

#### Main measurements

* Base-model score on the Adige evaluation set
* Fine-tuned score
* Human-rated correctness
* Human-rated naturalness
* Translation quality
* Cyrillic consistency
* Language-mixing frequency
* Performance by task type
* Performance versus training-data quantity

This experiment is significantly harder than Turkish fine-tuning because the central challenge becomes not only training the model, but also constructing trustworthy training and evaluation data.

---

### 3. Efficient Tiny Assistant

- **Model:** `Qwen3.5-4B` (see model-choice note below — `0.8B` deferred)
- **Stage 1:** SFT
- **Stage 2:** Preference optimization / RLHF-style methods
- **Primary objective:** useful information per generated token

**Model choice note:** this was originally planned for `Qwen3.5-0.8B`. It now
starts on `Qwen3.5-4B` instead, for two reasons: (1) this is precisely the
weakness the Turkish-capability baseline surfaced empirically (experiment 1's
outcome), and the diagnostic infrastructure and reused baseline are already on
4B; (2) `0.8B` genuinely risks being too weak to reliably learn a new
communication policy while the training/dataset methodology is still being
proven — debugging a new dataset and a much smaller model at the same time is
a harder problem than this project should take on yet. `0.8B` is not
abandoned; it's deferred to later, once this experiment's dataset and method
are validated on 4B and the project has more fine-tuning experience to spend
on a harder target. Tracked in `experiments/response-style-control/`.

The third experiment moves away from language acquisition and focuses on **behavioral specialization**.

The question becomes:

> Can a 0.8B model be trained to behave like an extremely efficient technical assistant?

Most general-purpose assistants frequently generate more text than necessary.

A response may contain:

```text
Acknowledgement
→ Restatement of the question
→ Background
→ Several headings
→ Main answer
→ Caveats
→ Repeated explanation
→ Summary
```

The desired assistant should instead behave approximately like:

```text
Question
   ↓
Best direct answer
```

The objective is not simply to make responses short.

It is to maximize **information density while preserving correctness and completeness**.

The model should learn a communication policy based on:

* direct answers,
* high information density,
* minimal conversational overhead,
* no unnecessary flattery,
* no canned acknowledgements,
* no repeated restatement of the question,
* no unnecessary introductions,
* no redundant conclusions,
* no automatic summary of content that was already concise,
* minimal headings and lists unless structure genuinely improves comprehension,
* a single coherent paragraph by default,
* natural conversational language,
* preservation of technical details,
* minimal token usage without meaningful information loss.

For example, the target is not:

```text
That's a great question. There are several important considerations here.
Let's break this down step by step...
```

Nor is the target simply:

```text
Yes.
```

The desired behavior is:

```text
A concise answer containing essentially all information necessary to correctly
answer the question, with minimal structural or conversational overhead.
```

#### Lossless Technical Condensation

A major component of the dataset will be **lossless technical condensation**.

A teacher model can generate a detailed technical answer and then transform it into a shorter version while attempting to preserve every materially useful fact.

Conceptually:

```text
Verbose high-quality answer
            ↓
Semantic condensation
            ↓
Short information-dense answer
```

The training pair can then teach the model that verbosity itself is not desirable.

For example:

```text
500-token technical answer
            ↓
150-token condensed target
```

The target should retain the same important:

* facts,
* constraints,
* warnings,
* assumptions,
* conclusions,
* technical distinctions.

This creates a more meaningful optimization target than simply minimizing response length.

#### Stage 1 — Supervised Fine-Tuning

The first stage will use SFT to establish the response style.

Training data can contain:

```text
User question
+
Direct, technically complete, compressed response
```

Preference examples may also be generated during this stage:

```text
Preferred:
Direct + complete + dense

Rejected:
Verbose + repetitive
```

However, the initial experiment should keep SFT and preference optimization conceptually separate so their individual effects can be measured.

#### Stage 2 — Preference Optimization

After establishing a reasonable SFT model, preference-learning approaches such as DPO or other RLHF-family methods can be studied.

The reward/preference objective should **not simply prefer the shortest response**.

That would quickly teach the model to omit useful information.

Instead, preferences should jointly reward:

```text
Correctness
+ Completeness
+ Information density
+ Directness
+ Technical usefulness
- Redundancy
- Filler
- Unnecessary tokens
```

The broader research question becomes:

> How much useful information can a 0.8B model deliver per generated token?

This makes the project particularly relevant to local and on-device inference, where latency, memory, battery consumption, and output-token generation costs all matter.

#### Evaluation

Useful metrics may include:

* factual correctness,
* task accuracy,
* semantic similarity to a full reference answer,
* important-fact recall,
* generated token count,
* compression ratio,
* information retained after compression,
* latency,
* tokens per second,
* invalid or incomplete answer rate.

A useful composite concept is:

```text
Useful correct information
──────────────────────────
Generated tokens
```

The goal is therefore not merely a tiny model.

It is an **efficient tiny model**.

---

### 4. TDD-Specialized Coding Agent

- **Model:** `Qwen3.5-4B`
- **Target:** Test-Driven Development
- **Training:** agent trajectories / supervised behavioral specialization

The final experiment moves from response behavior to procedural and agentic behavior.

Instead of creating another general coding assistant, the model will be specialized around one software-engineering workflow:

**Test-Driven Development.**

The central question is:

> Can a relatively small model become unusually competent at software development if almost all of its training focuses on one disciplined workflow?

The desired behavioral loop is approximately:

```text
Understand requirement
        ↓
Inspect relevant code
        ↓
Write or modify test
        ↓
Run test
        ↓
Observe failure
        ↓
Implement minimum required change
        ↓
Run test
        ↓
Pass?
   ↙          ↘
 No           Yes
 ↓             ↓
Diagnose      Refactor if needed
 ↓             ↓
Repair        Run regression tests
 └──────→ repeat
```

The defining characteristic is that the model should strongly prefer **test-first behavior**.

When given a bug report or feature request, its default action should not immediately be editing implementation code.

Instead it should attempt to:

1. understand the expected behavior,
2. locate the relevant code,
3. inspect existing tests,
4. construct a failing regression test,
5. verify that the test actually fails,
6. implement the smallest reasonable fix,
7. rerun the targeted test,
8. diagnose failures,
9. iterate until passing,
10. execute broader regression tests.

The model therefore learns a **development policy**, not merely code completion.

#### Training Data

Training data should ideally consist of successful TDD trajectories collected from repositories.

A trajectory might contain:

```text
Issue
↓
Repository inspection
↓
Relevant file discovery
↓
Test creation
↓
Test execution
↓
Failure output
↓
Implementation change
↓
Test execution
↓
Failure diagnosis
↓
Repair
↓
Passing test
↓
Regression test execution
```

Unsuccessful trajectories can also be useful if they are converted into preference data where the model learns which actions were inefficient or incorrect.

Potential tool actions include:

* listing files,
* searching code,
* reading files,
* writing tests,
* editing source code,
* executing tests,
* reading stack traces,
* inspecting diffs,
* reverting incorrect changes.

#### Evaluation

The model should be evaluated on previously unseen repositories and tasks.

Metrics can include:

* task completion rate,
* tests passed,
* regression rate,
* percentage of tasks where a test was written before implementation,
* percentage of generated tests that genuinely fail before the fix,
* number of tool calls,
* number of repair iterations,
* generated-token count,
* wall-clock completion time,
* unnecessary-edit rate,
* patch size.

The interesting comparison is not only:

```text
Base 4B vs TDD-fine-tuned 4B
```

but also:

```text
Generic coding behavior
vs
TDD-specialized behavior
```

A sufficiently specialized 4B model may be able to compete surprisingly well with substantially larger general-purpose models within this constrained workflow.

---

## Overall Progression

These four experiments deliberately increase in conceptual difficulty:

```text
1. Turkish
   ↓
Improve an existing language capability

2. Adige
   ↓
Acquire/improve a low-resource language through synthetic cross-lingual data

3. Efficient Assistant (starts on 4B, 0.8B deferred)
   ↓
Learn a highly constrained communication and optimization policy

4. TDD Coding Agent
   ↓
Learn a multi-step procedural policy involving tools, execution and feedback
```

Another way to view the progression is:

| Experiment          | Model        | What is being taught?               | Main difficulty                                        |
| ------------------- | ------------ | ----------------------------------- | ------------------------------------------------------ |
| Turkish             | Qwen3.5-4B   | Language capability (found: not the actual gap) | Evaluation and dataset quality             |
| Adige               | Qwen3.5-4B   | Low-resource language capability    | Data creation and validation                           |
| Efficient Assistant | Qwen3.5-4B (0.8B deferred) | Communication policy and efficiency | Multi-objective preference optimization  |
| TDD Agent           | Qwen3.5-4B   | Agentic procedural behavior         | Trajectory generation and environment-based evaluation |

Together, these experiments cover four important uses of post-training:

**capability improvement → low-resource adaptation → behavioral alignment → agent specialization.**

The common experimental principle across all four projects is simple:

> Every fine-tuning run should begin with a measurable baseline, modify one clearly defined capability or behavior, and finish with an evaluation capable of showing whether that capability actually improved.

A successful training run is therefore not defined by decreasing loss.

It is defined by measurable improvement on the behavior the experiment was designed to teach.

The ongoing 4B research-question program, including the three-day pilot cadence,
experiment template, and future architecture/agent questions, is tracked in
[`experiments/response-style-control/qwen3.5-4b/research-question-program.md`](experiments/response-style-control/qwen3.5-4b/research-question-program.md).
