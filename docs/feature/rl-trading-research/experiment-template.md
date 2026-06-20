# Experiment Card Template

> 上级：[`README.md`](README.md)

复制本模板用于记录单次 RL trading research 实验。实验卡是轻量 trace，不替代 `outputs/`、`models/` 原始产物，也不触发 taskBoard。

```markdown
# Experiment Card: <slug>

> 上级：[`experiment-ledger.md`](experiment-ledger.md)

## Hypothesis

一句话说明本实验为什么可能改善 validation / walk-forward OOS。

## Scope

- Direction: feature / reward / bracket / PPO / cost / timeframe / evaluation / visualization
- Owner files:
- What changes:
- What stays frozen:
- Holdout status: not used / frozen-only / already revealed

## Baseline Evidence

- Previous run or artifact:
- Known problem:
- Relevant metrics:
- Relevant charts:

## Change Plan

- Code/config changes:
- Expected behavior:
- Risk:

## Validation Plan

- G0 setup:
- G1 pipeline:
- G2 baseline sanity:
- G3 PPO walk-forward:
- G4 consistency gate:
- G5 frozen holdout: not part of this loop unless explicitly frozen

## Results

- Artifacts:
- total_return / annualized_return:
- max_drawdown:
- profit_factor:
- sharpe_like:
- n_trades:
- fold consistency:
- NO_DEPLOY:

## Feedback

- Decision: accept / reject / inconclusive
- Reason:
- New knowledge:
- Next hypothesis:
```

## Use Rules

- 一张实验卡只记录一个主要研究方向。
- 如果同时改了多个方向，必须解释为什么不可拆分。
- 不把 sealed holdout 作为普通验证步骤。
- 重要结论写入 [`experiment-ledger.md`](experiment-ledger.md)，稳定决策再沉淀到 [`decisions.md`](decisions.md)。
