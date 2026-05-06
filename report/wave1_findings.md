# Wave 1 Findings (post-fixes)

Source data: [src/results-wave1-fixed/](../src/results-wave1-fixed/).
Coverage: 12 cells = {llama8, qwen25} × {blocksworld, citycar, tetris} × {baseline, cot}, 20 instances each, up to 4 iterations with stop-on-success.

## 1. Headline numbers

| cell | solved | mean valid_action% (all iters) | mean valid_action% (iter 1) |
|---|---:|---:|---:|
| llama8/blocksworld/baseline | 0/20 | 10.8% | 6.3% |
| llama8/blocksworld/cot      | 0/20 | 23.4% | 20.4% |
| llama8/citycar/baseline     | 0/20 |  5.5% |  6.3% |
| llama8/citycar/cot          | 0/20 | 10.1% |  6.5% |
| llama8/tetris/baseline      | 0/20 | 12.1% | 10.9% |
| llama8/tetris/cot           | 0/20 | 12.4% | 12.9% |
| qwen25/blocksworld/baseline | **2/20** | 17.8% | 18.6% |
| qwen25/blocksworld/cot      | **3/20** | 31.0% | 28.1% |
| qwen25/citycar/baseline     | 0/20 | 23.3% | 14.8% |
| qwen25/citycar/cot          | 0/20 |  9.3% |  4.8% |
| qwen25/tetris/baseline      | 0/20 |  1.5% |  1.0% |
| qwen25/tetris/cot           | 0/20 | 13.1% | 13.6% |

**5 full solves total, all on qwen25/blocksworld.** Llama-3.1-8B did not solve a single instance across any of the 6 (domain, condition) pairs.

Solve traces:

| cell | instance | iteration |
|---|---|---:|
| qwen25/blocksworld/baseline | instance-02 | 3 |
| qwen25/blocksworld/baseline | instance-05 | 1 |
| qwen25/blocksworld/cot      | instance-04 | 1 |
| qwen25/blocksworld/cot      | instance-05 | 3 |
| qwen25/blocksworld/cot      | instance-06 | 1 |

3 of 5 solves come from iteration 1; the other 2 come from iteration 3 (re-prompted with VAL feedback). None come from iterations 2 or 4 — small-N, but consistent with the qualitative observation that iteration is hit-or-miss rather than monotonic.

## 2. The new important finding: failure-mode decomposition

`plan_len` in the CSV is VAL's reported "Plan size:", not the Python extractor's row count, so a row with `plan_text` full of actions but `plan_len=0` means **VAL refused to parse the plan** (action signature mismatch, type mismatch, or syntactic rejection). This is a different failure from "the model produced no plan at all". Splitting the rows three ways:

- **empty**: `plan_text` is empty. The postprocessor's allowlist filter dropped every paren-prefixed line the model emitted because none matched the domain's declared action names. Verified on `qwen25/tetris/baseline/instance-01`: the model emitted ~380 tokens of `(clear f4-0f)`, `(at_square square0 f0-0f)`, `(at_two straight0 f0-2f f1-2f)` — state predicates, not actions. Tetris actions are `move_square`, `move_two`, `move_l_down`, etc., so all lines were correctly filtered. This is the model **misreading the task and echoing the initial state** instead of producing an action sequence; CoT fixes it by explicitly telling the model to produce actions.
- **parse_fail**: `plan_text` is non-empty but `plan_len == 0`. VAL halted before reporting plan size — typically because the plan referenced an object that isn't declared in the problem. Verified by re-running VAL on `qwen25/citycar/cot/instance-02`: the plan references `road5`/`road6` but the problem only declares `road0`–`road4`, and VAL reports `Object with unknown type: road5`. This is the model **hallucinating objects** that don't exist in the problem, not a validator setup bug.
- **partial**: `plan_len > 0` but `solves_problem == False` (VAL parsed, plan didn't reach the goal).
- **solved**: `solves_problem == True`.

Distribution across all iterations:

| cell | empty | parse_fail | partial | solved |
|---|---:|---:|---:|---:|
| llama8/blocksworld/baseline |  1% | 12% | 86% |  0% |
| llama8/blocksworld/cot      |  2% |  2% | 95% |  0% |
| llama8/citycar/baseline     | 19% | 40% | 41% |  0% |
| llama8/citycar/cot          | 11% | 24% | 65% |  0% |
| llama8/tetris/baseline      | 19% | 15% | 67% |  0% |
| llama8/tetris/cot           |  7% | 28% | 65% |  0% |
| qwen25/blocksworld/baseline | 11% |  0% | 87% |  3% |
| qwen25/blocksworld/cot      |  3% |  0% | 93% |  4% |
| qwen25/citycar/baseline     |  7% | 32% | 61% |  0% |
| qwen25/citycar/cot          | 10% | **60%** | 29% |  0% |
| qwen25/tetris/baseline      | **70%** | 11% | 20% |  0% |
| qwen25/tetris/cot           |  0% |  6% | 94% |  0% |

What this reveals:

- **Blocksworld is a different problem from citycar/tetris.** Both models reach VAL parse-success >85% of the time on blocksworld. On the harder domains, VAL parse-failure dominates (citycar: 24–60%; tetris parse-fail or empty: 11–70%).
- **qwen25/tetris/baseline collapses at the *prompt* layer, not at planning.** 70% of rows have empty `plan_text` — the model under the baseline prompt is not emitting recognizable PDDL action lines on tetris at all. CoT *fixes* this completely (0% empty, 94% partial), which is why the headline metric jumps 1.5% → 13.1%. This is not "CoT helps the model reason" — it is "CoT gets the model to emit a plan in the first place." Worth flagging in the discussion.
- **qwen25/citycar moves in the opposite direction under CoT.** Parse-failure rises 32% → 60%; partial drops 61% → 29%. Re-running VAL on a parse-fail row confirms the failure mode: the model invents object names (e.g., `road5`, `road6`) that aren't declared in the problem, and VAL halts at `Object with unknown type: road5` before reporting plan size. The CoT scratchpad on this domain × model appears to encourage the model to plan past the available roads and build new ones with names that don't exist. Worth one paragraph in the Discussion as a concrete example of CoT going wrong.
- **llama8 spreads its failures across all three buckets**; qwen25 concentrates failure in one bucket per cell. That is the more meaningful "intra-family vs cross-family" qualitative difference than the raw vap%.

## 3. Iteration dynamics

Per-iteration mean valid_action_percent (cells where `n_iter == 1` rows is suppressed by stop-on-success or run abort):

| cell | iter 1 | iter 2 | iter 3 | iter 4 |
|---|---:|---:|---:|---:|
| llama8/blocksworld/baseline |  6.3% | 10.5% | 13.3% | 12.9% |
| llama8/blocksworld/cot      | 20.4% | 25.2% | 27.6% | 20.6% |
| llama8/citycar/baseline     |  6.3% |  6.6% |  3.6% |  5.0% |
| llama8/citycar/cot          |  6.5% |  8.6% | 16.7% |  9.6% |
| llama8/tetris/baseline      | 10.9% | 14.4% | 11.4% | 11.4% |
| llama8/tetris/cot           | 12.9% | 16.4% |  9.2% |  9.5% |
| qwen25/blocksworld/baseline | 18.6% | 17.6% | 20.5% | 14.3% |
| qwen25/blocksworld/cot      | 28.1% | 28.4% | 36.4% | 31.4% |
| qwen25/citycar/baseline     | 14.8% | 17.0% | 38.8% | 24.4% |
| qwen25/citycar/cot          |  4.8% | 13.9% |  8.6% | 10.1% |
| qwen25/tetris/baseline      |  1.0% |  1.7% |  0.8% |  2.4% |
| qwen25/tetris/cot           | 13.6% | 11.7% | 13.9% | 13.4% |

Per-instance delta from iter 1 to last seen iter (not mean of means — this counts how often re-prompting *that specific instance* helps, helps_or_same, or hurts):

| cell | better | same | worse | mean Δ |
|---|---:|---:|---:|---:|
| llama8/blocksworld/baseline |  7 |  5 |  8 |  +6.6 pp |
| llama8/blocksworld/cot      |  8 |  7 |  5 |  +0.2 pp |
| llama8/citycar/baseline     |  2 |  9 |  8 |  −2.7 pp |
| llama8/citycar/cot          |  2 |  7 | 11 |  +1.7 pp |
| llama8/tetris/baseline      |  6 |  5 |  9 |  −1.2 pp |
| llama8/tetris/cot           |  2 |  6 |  8 |  −9.6 pp |
| qwen25/blocksworld/baseline | 10 |  5 |  4 |  +4.5 pp |
| qwen25/blocksworld/cot      | 12 |  4 |  2 | **+15.0 pp** |
| qwen25/citycar/baseline     |  6 |  6 |  8 |  +5.9 pp |
| qwen25/citycar/cot          |  2 | 13 |  5 |  +4.3 pp |
| qwen25/tetris/baseline      |  2 | 14 |  1 |  +0.7 pp |
| qwen25/tetris/cot           |  1 | 12 |  6 |  −3.0 pp |

**Iteration is helpful where the model already has traction, and noisy or harmful where it doesn't.** qwen25/blocksworld/cot moves +15 pp on average and includes both iter-3 solves; in contrast, llama8/tetris/cot gets *worse* by 9.6 pp on average across iterations. The proposal's "iteration-gain curves" plot should be cell-conditional, not aggregated, since the sign flips.

A second methodological note for the limitations section: with stop-on-success, instances solved at iter 1 don't appear in the iter 2–4 rows at all, so simply averaging vap by iteration confounds two effects (model ability + selection of harder remaining instances). The per-instance delta table above is the version that controls for it.

## 4. CoT vs baseline

| cell (model/domain) | baseline mean vap | cot mean vap | Δ | base solves | cot solves |
|---|---:|---:|---:|---:|---:|
| llama8/blocksworld | 10.8% | 23.4% | **+12.7 pp** | 0 | 0 |
| llama8/citycar     |  5.5% | 10.1% |  +4.6 pp | 0 | 0 |
| llama8/tetris      | 12.1% | 12.4% |  +0.4 pp | 0 | 0 |
| qwen25/blocksworld | 17.8% | 31.0% | **+13.2 pp** | 2 | 3 |
| qwen25/citycar     | 23.3% |  9.3% | **−14.0 pp** | 0 | 0 |
| qwen25/tetris      |  1.5% | 13.1% | **+11.6 pp** | 0 | 0 |

Five of six (model, domain) cells show CoT helping — but it helps for *different reasons*:

- On blocksworld for both models, CoT raises the rate at which VAL accepts a plan as well-formed (partial+solved climbs).
- On qwen25/tetris, CoT mostly fixes the "model emits no plan" failure (empty drops 65% → 0% at iter 1).
- On qwen25/citycar, CoT *hurts* — at iter 1 alone, baseline is 14.8% and CoT is 4.8%. Failure-mode breakdown (above) shows CoT shifts mass from "partial plan" into "VAL parse failure", suggesting the chain-of-thought scratchpad is leaking malformed action signatures into the final plan block on this particular domain. Worth a per-prompt diff investigation against the qwen25/citycar/baseline prompt before generalizing the CoT-is-good claim.

The earlier "CoT hurts llama8" claim from the broken-baseline wave 1 has been *reversed* with the fixes: llama8 now sees +0.4 to +12.7 pp from CoT across all three domains.

## 5. Plan length, token usage, max_new_tokens cap

The bump from 4096 → 8192 was needed but is **still not enough** for llama8 on the harder domains:

| cell | mean comp_tok | median | max | p95 | rows ≥ 8000 (cap hits) |
|---|---:|---:|---:|---:|---:|
| llama8/blocksworld/baseline |  721 |  320 | 8192 | 1324 |  4 |
| llama8/blocksworld/cot      |  647 |  204 | 8192 | 1781 |  3 |
| llama8/citycar/baseline     | 2033 |  898 | 8192 | 8192 | **11** |
| llama8/citycar/cot          | 2225 | 1146 | 8192 | 8192 | **11** |
| llama8/tetris/baseline      | 2610 | 1818 | 8192 | 8192 |  9 |
| llama8/tetris/cot           | 3506 | 2350 | 8192 | 8192 |  9 |
| qwen25/blocksworld/baseline |  120 |   88 | 1270 |  231 |  0 |
| qwen25/blocksworld/cot      |  178 |  100 |  664 |  518 |  0 |
| qwen25/citycar/baseline     | 1555 |  475 | 8192 | 8192 | 10 |
| qwen25/citycar/cot          |  691 |  554 | 8192 | 1478 |  1 |
| qwen25/tetris/baseline      | 1605 | 1686 | 4161 | 2503 |  0 |
| qwen25/tetris/cot           | 2209 | 2295 | 3497 | 3146 |  0 |

Cap-conditional vap (when cap is hit, the model is in "ramble mode" and the extracted plan rarely reaches VAL's plan-size threshold):

| cell | n_capped | vap_capped | vap_uncapped |
|---|---:|---:|---:|
| llama8/blocksworld/baseline |  4 |  0.9% | 11.3% |
| llama8/blocksworld/cot      |  3 |  0.0% | 24.4% |
| llama8/tetris/baseline      |  9 |  0.0% | 13.7% |
| llama8/tetris/cot           |  9 |  2.4% | 14.2% |
| qwen25/citycar/baseline     | 10 | 18.4% | 24.1% |

The cap is selecting against valid plans on llama8, less so on qwen25/citycar. Two interpretations: (a) llama8 actually needs a higher cap on tetris/citycar to ever finish; (b) llama8's verbosity is itself the failure mode (the plan does appear early in the response, but the model then rambles past it and the extractor can't disambiguate). Either way, the cap correlates strongly with non-completion and should be reported.

qwen25 on blocksworld is shockingly token-efficient: 6 completion tokens per VAL-parsed action. That is essentially "no scratchpad, just emit the plan." This is why qwen25 is the only model with solves and is worth its own sentence in the discussion.

## 6. Wallclock totals (for reproducibility section)

| cell | total minutes | mean s/iter |
|---|---:|---:|
| llama8/blocksworld/baseline |  27.8 |  20.9 |
| llama8/blocksworld/cot      |  23.3 |  17.4 |
| llama8/citycar/baseline     |  69.4 |  59.5 |
| llama8/citycar/cot          |  79.5 |  64.4 |
| llama8/tetris/baseline      |  93.4 |  74.7 |
| llama8/tetris/cot           | 102.3 | 102.3 |
| qwen25/blocksworld/baseline |  11.9 |   9.4 |
| qwen25/blocksworld/cot      |  16.2 |  13.3 |
| qwen25/citycar/baseline     | 172.8 | 138.3 |
| qwen25/citycar/cot          |  73.5 |  56.5 |
| qwen25/tetris/baseline      | 144.1 | 131.0 |
| qwen25/tetris/cot           | 215.2 | 181.9 |

Wave 1 (12 cells) total: ~17.6 hours of wallclock.

## 6b. Domain inventory (selected 6 domains)

The selected domains for the controlled study, with structural complexity (parsed from each `domain.pddl`) and minimum plan length (length of the optimal or near-optimal solver plan we authored to validate each instance is solvable). For wave-1 domains, the empirical column is the wave-1-redo data above; for the wave-3 additions (basic_move, visit-all, satellite) the empirical column is left blank until those cells run.

| domain | source | #actions | max action arity | #types | n instances | hand-authored plan length | empirical solves (wave 1, qwen25 only) | predicted tier |
|---|---|---:|---:|---:|---:|---:|---|---|
| basic_move  | this project — directed-graph traversal | 1 | 2 | 0 | 10 | 1–7 (mean 4.2)   | — | **easiest** |
| visit-all   | this project — IPC-2014 formulation     | 1 | 2 | 1 | 10 | 2–10 (mean 5.4)  | — | **easiest** |
| blocksworld | Project A (Merola et al.)               | 4 | 2 | 0 | 20 | n/a (5 solves; plans 6–8 actions) | 5/120 | easy |
| satellite   | this project — IPC-2002 formulation     | 5 | 4 | 4 | 10 | 5–18 (mean 9.8)  | — | medium |
| citycar     | Project B (D'Ascenzo & Gentili)         | 7 | 4 | 4 | 20 | n/a (no solves; mean-best vap 26%) | 0/120 | medium-hard |
| tetris      | Project B (D'Ascenzo & Gentili)         | 6 | 7 | 6 | 20 | n/a (no solves; mean-best vap 12%) | 0/120 | hardest |

How to read the columns:

- **#actions** is the count of `(:action …)` blocks in `domain.pddl`. More actions = larger output vocabulary the model has to ground correctly.
- **max action arity** is the largest action's parameter count. From the wave-1 data this is the best single predictor of VAL parse-failure rate (citycar arity-4 → 24–60% parse_fail; tetris arity-7 → 70% empty-plan rate on qwen25/baseline).
- **#types** is the size of the `(:types …)` declaration. More types = more chances for the model to ground an object to the wrong type, which causes VAL to halt with `Object with unknown type: <X>`.
- **hand-authored plan length** is the number of actions in the optimal / near-optimal plan we wrote and validated against VAL for each of the 10 instances. This is the *floor* — what a perfect planner would produce. Models that generate plans much shorter than this floor are emitting under-complete plans; models whose plans grow much longer are likely padding with redundant actions.
- **predicted tier** ranks how hard we expect the domain to be for an LLM, combining structural complexity above with training-data familiarity (basic_move/visit-all/satellite/blocksworld are textbook PDDL domains; citycar and tetris are far less common in pretraining corpora).

The new domains slot into the difficulty range below blocksworld (basic_move, visit-all) and roughly between blocksworld and citycar (satellite). This gives us a difficulty gradient over 6 cells instead of 3, and lets us answer "do these models fail because they can't plan, or because they can't read these specific PDDL dialects?" — if the easiest-tier domains see solve rates well above 0, the wave-1 zero-solve cells reflect domain-unfamiliarity more than fundamental planning inability.

## 7. Domain difficulty ranking

Both models, both conditions, agree on:

**blocksworld < citycar ≈ tetris**

- blocksworld: only domain with solves; lowest VAL parse-fail rate; shortest plans; both models fluent in action signatures.
- citycar: high VAL parse-fail (24–60%), suggesting action signatures (4-arg actions like `move_car_in_road`) are harder to ground correctly. qwen25/citycar/baseline mean-best vap is 45% across instances — the model gets *close* repeatedly but never finishes.
- tetris: highest variance across cells. qwen25/tetris/baseline collapses to empty plans, but qwen25/tetris/cot looks like a normal hard cell. The asymmetry here is a prompt-format effect, not a domain-difficulty effect.

## 8. Things to note in the Limitations section

These follow from the data above and from the previously-flagged caveats:

1. **plan_len=0 ambiguity.** A non-empty plan with VAL Plan size: 0 should be reported as a separate failure category, not collapsed into "0% valid actions." Our headline mean-vap numbers slightly understate model performance on cells with high parse-fail rates, because parse-fail rows contribute 0% to the mean.
2. **Stop-on-success selection bias** in iteration 2–4. Per-iteration vap should not be read as "the model gets better/worse over time" without conditioning on instance.
3. **CoT effect is not single-signed.** It improves 5/6 cells but degrades qwen25/citycar substantially. The mechanism is different across domains (helps reasoning vs. forces emission of a plan vs. corrupts action signatures). Don't aggregate these into a single "CoT helps" claim.
4. **llama8 fills the 8192 cap on citycar/tetris** in 9–11 of 20 instances. The 8192 → 16384 jump should be tested before drawing strong conclusions about llama8 on hard domains.
5. **qwen25/citycar regression under CoT** likely reflects a prompt-format issue specific to that domain × model × condition triple. Inspecting the `cot_citycar` prompt against `cot_blocksworld` is the cheapest next debugging step.
6. **Seed plumbing was fixed mid-experiment**; CUDA non-determinism remains. These wave-1-redo numbers are the "seeded" reference; comparisons across runs of the same cell still have small variance.
7. **5 solves, all qwen25/blocksworld.** The proposal's success-rate matrix will be sparse, and any claim about model ability on citycar/tetris must rely on partial-credit metrics (vap, consecutive_valid_steps) rather than solve-rate.

## 9. Suggested figures for the headline matrix

Now informed by what's actually in the data:

1. **Failure-mode stacked bar** per (model, domain, condition) — empty / parse_fail / partial / solved. This is the most novel chart and immediately conveys the qwen25/tetris/baseline and qwen25/citycar/cot anomalies.
2. **CoT delta per cell**, with 95% CI (paired by instance using mean of all iterations). Shows CoT's sign flip on qwen25/citycar.
3. **Per-instance iteration delta** scatter (iter 1 vap on x-axis, last-iter vap on y-axis), one panel per cell. Shows iteration helps the strong cells and hurts the weak ones.
4. **Plan-length / completion-tokens scatter**, color-coded by cell, with the 8192 cap drawn as a horizontal line. Demonstrates the llama8 cap problem visually.
5. **Best-of-iter vap** vs solve-rate, per cell — there's a long gap between "model gets all actions valid" (max=100% in 7/12 cells) and "model solves the problem" (5 total solves), which is itself a finding about goal-directed planning vs. action-grounding.

## 10. Reproducing these numbers

```python
import pandas as pd, glob, os

dfs=[pd.read_csv(f) for f in sorted(
    glob.glob('src/results-wave1-fixed/**/run_metrics.csv', recursive=True))]
df = pd.concat(dfs, ignore_index=True)
df['plan_text'] = df['plan_text'].fillna('')
df['empty_plan']      = df['plan_text'].str.strip() == ''
df['val_parse_fail']  = (~df['empty_plan']) & (df['plan_len']==0)
df['val_partial']     = (df['plan_len']>0) & (~df['solves_problem'])
df['hit_cap']         = df['completion_tokens'] >= 8000
```

Every table in this document is regenerable from the snippet above plus the groupby chains shown in the conversation log.
