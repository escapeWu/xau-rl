# Project Memory

> 上级：[`INDEX.md`](INDEX.md)

本文件记录跨模块、长期有效的项目记忆。它不是实验日志；单次实验索引见 [`../feature/rl-trading-research/experiment-ledger.md`](../feature/rl-trading-research/experiment-ledger.md)，RL 模块稳定决策见 [`../feature/rl-trading-research/decisions.md`](../feature/rl-trading-research/decisions.md)。

## Always Remember

- 本项目是 XAUUSD RL trading research framework，不是收益承诺系统。
- 先看配置、代码、产物、图表和 fold 指标，再给结论。
- Sealed holdout 只在模型、配置和评估口径冻结后揭盲一次。
- 成本假设是结果可信度的一部分；spread/slippage/commission 不可信时，收益曲线不能当真。
- 特征必须因果：每个 timestamp 只能使用当前及过去已经完成的 bar。
- `models/NO_DEPLOY.txt` 存在时，run 默认 research-only。

## Current Research Stance

- 日常迭代使用 validation 和 sliding walk-forward OOS，不使用 sealed holdout 调参。
- Baseline 是 PPO 结论的 sanity comparator；RL 结果应在同一 split/window 语境下与 baseline 比较。
- 交易次数太少时，PF、win rate、return 都不稳定。
- 多 fold OOS 一致性比单次漂亮 equity curve 更重要。

## Stable Project Decisions

| Date | Decision | Scope | Reason |
|------|----------|-------|--------|
| 2026-06-21 | 使用 `.agent` 而不是 `.cursor` | skills / harness | 保持通用目录，避免绑定工具专有路径 |
| 2026-06-21 | 不初始化 taskBoard / tasks WIP | harness | 本项目当前使用轻量 stage gates 更合适 |
| 2026-06-21 | R&D loop 不包含 sealed holdout | research protocol | 防止 holdout 被迭代污染 |
| 2026-06-21 | 原始实验结果留在 `outputs/` 与 `models/` | artifacts | docs 只记录路由、口径、索引和稳定结论 |

## Known Pitfalls

| Pitfall | Symptom | Check |
|---------|---------|-------|
| timestamp open/close 错位 | 交易点、图表或成交整体差一个 bar | `timestamp_is_bar_open`, `source_tz` |
| 成本设置过低 | 回测收益显著虚高 | `spread_price`, `slippage_price`, `commission_per_trade` |
| 交易次数过少 | PF/return 看起来很好但不可复现 | `n_trades`, trade log |
| 单个 fold 暴赚 | 平均值好看但跨时期不稳定 | per-fold summary, stitched OOS equity |
| 忽略 VecNormalize | 模型评估异常或不可复现 | `best_model.zip` 与 `best_model_vecnorm.pkl` 是否成对存在 |

## Superseded / Deprecated

- 不再使用 Cursor 专用 skills 路径作为项目 skill 路径；当前统一使用 `.agent/skills/...`。
- 不使用 taskBoard/tasks WIP 机制初始化本项目。
- 不把 `final_holdout_eval.py` 当 validation 循环入口。

## Update Rule

只有长期有效、跨实验仍成立、会影响后续 agent 行为的内容才写入本文件。一次性实验结果进入 experiment ledger 或 archive，不进入 project memory。
