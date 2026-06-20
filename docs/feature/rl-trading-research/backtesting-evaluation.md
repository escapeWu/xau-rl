# Backtesting and Evaluation

> 上级：[`README.md`](README.md)

本文件整理本项目回测与评估的稳定口径。更细的 agent 操作提示见 [`.agent/skills/rl-trading-training/references/backtesting-evaluation.md`](../../../.agent/skills/rl-trading-training/references/backtesting-evaluation.md)。

## Evaluation Layers

本项目至少区分三类评估，不能混用结论。

### Validation-only Baseline

入口：

```bash
python run_pipeline.py
```

用途：验证数据、特征、baseline 和图表流程是否可信。关键产物：

```text
outputs/performance_report.csv
outputs/selected_val_trade_log.csv
outputs/selected_val_equity_curve.csv
outputs/walk_forward_baseline.csv
```

该层是迭代期 sanity evidence，不是最终可部署证据。

### Sliding Walk-forward OOS

入口：

```bash
python train_ppo.py
```

用途：评估 PPO agent 在不同时期的 OOS 稳定性。关键产物：

```text
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/NO_DEPLOY.txt
```

训练研究期间，RL 结论优先基于这一层，而不是单个 split 或最后 checkpoint。

### Sealed Holdout

入口：

```bash
python final_holdout_eval.py
```

用途：模型冻结后一次性揭盲。关键产物：

```text
outputs/final_holdout/holdout_report.csv
outputs/final_holdout/rl_test_trade_log.csv
outputs/final_holdout/rl_test_equity_curve.csv
```

揭盲后不能继续根据 holdout 调参。

## Metrics to Read Together

不要只看 `total_return_pct`。至少同时检查：

- `annualized_return_pct`
- `max_drawdown_pct`
- `sharpe_like`
- `sortino_ratio`
- `calmar_ratio`
- `profit_factor`
- `win_rate_pct`
- `avg_r`, `median_r`
- `n_trades`
- `avg_bars_in_trade`

## Review Checklist

1. 交易次数是否足够。
2. 每个 fold 是否都可接受，而不是平均值被单折拉高。
3. 最差 fold 是否灾难性亏损。
4. OOS equity 是否由少数交易贡献。
5. drawdown 是否超过研究/部署承受范围。
6. baseline 与 RL 是否处于同一 split/window 语境。
7. `models/NO_DEPLOY.txt` 是否存在。

## Safe Result Wording

推荐表述：

```text
该结论来自 validation / sliding walk-forward OOS / sealed holdout。
关键指标包括 return、max DD、PF、Sharpe-like、n_trades。
当前 gate 状态是通过 / 未通过 / 证据不足。
部署状态是 deployable / research-only / cannot tell。
```

除非 validation、walk-forward、gate、成本和 sealed holdout 都支持，不要说“模型已经稳定盈利”。
