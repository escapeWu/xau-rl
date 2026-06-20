---
name: rl-trading-training
description: Guides RL-for-trading research in this XAUUSD PPO bracket-trading project. Use when the user asks how to train, evaluate, backtest, visualize, debug, or operationalize the RL trading workflow for this repository.
---

# RL Trading Training

Use this skill for questions or tasks about training and evaluating the RL trading agent in this repository.

This is a project-specific toolkit for the XAUUSD M1 -> decision-timeframe -> PPO bracket-trading workflow. Keep this entry file concise: load only the reference files needed for the current task.

This skill follows a harness-style, progressive-disclosure workflow: start from the small map, choose an execution mode, gather evidence from the relevant artifacts, then answer with explicit gates and next actions. It intentionally does not use taskboard or WIP task-board mechanics.

## When to use

- The user asks how to train, evaluate, backtest, visualize, or debug this RL trading project.
- The user asks whether a run is valid, deployable, overfit, or only research-grade.
- The user asks what to change in data, features, reward, PPO, costs, or walk-forward settings.
- The user asks for charts, reports, artifact interpretation, or run diagnostics.

## When not to use

- Pure Python syntax/style work unrelated to trading research.
- Generic finance/trading discussion not tied to this repository.
- Taskboard creation or taskboard maintenance workflows.

## Reference map

- Training workflow: `references/training-workflow.md`
- Backtesting and evaluation: `references/backtesting-evaluation.md`
- Chart visualization: `references/chart-visualization.md`
- Common pitfalls: `references/common-pitfalls.md`
- Harness operating modes: `references/operating-modes.md`
- Tooling and scripts: `references/toolkit.md`

## Default workflow

1. Classify the request: training plan, run diagnosis, backtest review, visualization, pitfall/debugging, or code-change planning.
2. Read `docs/USAGE_ZH.md` only when project context is needed, then read the most relevant reference file above.
3. Gather evidence before conclusions: config values, split/fold identity, artifact paths, metrics, charts, and `NO_DEPLOY` status.
4. Prefer validation/walk-forward outputs during iteration. Do not use sealed holdout repeatedly.
5. Use `scripts/rl_trading_doctor.py` for a lightweight artifact/config sanity check when diagnosing a run.

## Output expectations

When answering users, be explicit about:

- which split or fold is being discussed;
- whether an output is validation, walk-forward OOS, or sealed holdout;
- which artifacts to inspect next;
- whether the result is research-only or deployable under the consistency gate.

Use concise stage-gate language: `setup -> pipeline -> baseline -> PPO walk-forward -> frozen holdout`. Do not skip a gate in recommendations.
