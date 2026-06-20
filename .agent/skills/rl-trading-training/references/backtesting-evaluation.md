# 回测与评估参考

本参考用于回答“怎么回测”“怎么看报告”“validation、walk-forward、holdout 有什么区别”等问题。

## 回测层级

本项目有三类评估，不要混用结论。

### Validation-only baseline

入口：

```bash
python run_pipeline.py
```

用途：检查数据、特征、baseline、图表输出是否可信。它主要写 validation 输出，不应宣称为最终结果。

关键文件：

```text
outputs/performance_report.csv
outputs/selected_val_trade_log.csv
outputs/selected_val_equity_curve.csv
outputs/walk_forward_baseline.csv
```

### Sliding walk-forward OOS

入口：

```bash
python train_ppo.py
```

用途：评估 RL agent 跨时期稳定性。每个 fold 的 test window 是模拟真实部署的 out-of-sample 片段，拼接后形成 OOS equity。

关键文件：

```text
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/NO_DEPLOY.txt
```

这是训练研究期间最重要的 RL 评估来源。

### Sealed holdout

入口：

```bash
python final_holdout_eval.py
```

用途：模型冻结后的最终一次性揭盲。不要反复根据 holdout 调参。

关键文件：

```text
outputs/final_holdout/holdout_report.csv
outputs/final_holdout/rl_test_trade_log.csv
outputs/final_holdout/rl_test_equity_curve.csv
```

## 必看指标

不要只看收益。至少同时检查：

- `total_return_pct`：总收益。
- `annualized_return_pct`：按决策周期年化后的收益。
- `max_drawdown_pct`：最大回撤。
- `sharpe_like`：简化 Sharpe-like 指标。
- `sortino_ratio`：下行波动惩罚。
- `calmar_ratio`：年化收益 / 最大回撤。
- `profit_factor`：总盈利 / 总亏损。
- `win_rate_pct`：胜率。
- `avg_r`, `median_r`：每笔交易的 R 倍数。
- `n_trades`：交易样本数。
- `avg_bars_in_trade`：平均持仓长度。

## 推荐判断流程

1. 先看是否有足够交易次数。
2. 看每个 fold 是否都能接受，而不是只看平均值。
3. 看最差 fold 是否灾难性亏损。
4. 看 OOS equity 是否由少数几笔交易贡献。
5. 看 drawdown 是否超出策略可承受范围。
6. 与 baseline 在同一 split/window 上比较。
7. 检查是否通过 consistency gate。

## 常见红旗

- Train 很好，validation/OOS 很差：过拟合。
- 只有一个 fold 暴赚：可能是运气或行情特例。
- `n_trades` 很少但收益很高：统计不稳定。
- Profit factor 很高但交易很少：不可靠。
- 最大回撤接近或超过收益：路径风险过高。
- Long/short 极端偏一边：可能只是在某段单边行情有效。
- 成本参数很乐观：短线黄金回测容易被 spread/slippage 吞掉。

## Consistency gate

项目通过 gate 判断模型是否允许推广到 production artifact。相关配置在 `config.py`：

```python
min_consistent_folds
gate_min_profit_factor
gate_worst_fold_min_pf
gate_require_mean_sharpe_positive
```

如果存在：

```text
models/NO_DEPLOY.txt
```

则该 run 是研究结果，不是可部署策略。回答用户时要明确说明。

## 正确表述结果

推荐使用这种表述：

```text
该结果来自 sliding walk-forward OOS，不是 sealed holdout。
共 N 个 fold，其中 M 个 fold 满足 return>0 和 PF 门槛；最差 fold PF 为 X。
当前是否存在 NO_DEPLOY：是/否。
下一步建议检查 sliding_oos_equity 和每折 trade log。
```

避免：

```text
这个模型已经稳定盈利。
```

除非 walk-forward、gate、成本、holdout 都支持这个结论。
