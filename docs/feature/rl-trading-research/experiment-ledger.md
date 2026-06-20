# Experiment Ledger

> 上级：[`README.md`](README.md)

本文件是长期实验索引，记录每轮实验的方向、假设、artifact 和结论。不要在这里粘贴完整指标表；原始数据保留在 `outputs/` 与 `models/`。

## Ledger

| Date | Slug | Direction | Hypothesis | Artifacts | Decision | Notes |
|------|------|-----------|------------|-----------|----------|-------|
| _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | _pending_ | Use `experiment-template.md` for new experiments. |

## Direction Scoreboard

| Direction | Tried | Accepted | Rejected | Inconclusive | Common failure |
|-----------|-------|----------|----------|--------------|----------------|
| feature | 0 | 0 | 0 | 0 | leakage / collinearity |
| reward | 0 | 0 | 0 | 0 | sparse reward / overtrading |
| bracket | 0 | 0 | 0 | 0 | harder exploration / too few trades |
| PPO regularization | 0 | 0 | 0 | 0 | underfit / no trades / overfit |
| cost assumptions | 0 | 0 | 0 | 0 | result collapses under realistic costs |
| timeframe / split | 0 | 0 | 0 | 0 | incomparable windows / leakage risk |

## Decision Labels

- `accept`: evidence supports keeping or extending the direction.
- `reject`: evidence argues against this direction.
- `inconclusive`: evidence is insufficient, unstable, too sparse, or contaminated.

## Artifact Rules

- Use validation and walk-forward artifacts for iteration.
- Use sealed holdout artifacts only after model/config freeze.
- If `models/NO_DEPLOY.txt` exists, mark the run research-only unless later evidence explicitly changes status.
