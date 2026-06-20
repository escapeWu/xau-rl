# Interfaces and Artifact Contracts

> 上级：[`INDEX.md`](INDEX.md)

本文件记录输入数据、配置项和运行产物的稳定契约。字段细节以当前代码为准；本文用于帮助 agent 快速定位和验证。

## Raw Data Contract

默认数据路径来自 `config.py`：

```text
data/XAUUSD_1 Min_Bid_2003.05.05_2026.05.31.csv
```

CSV 至少应包含：

```csv
Time (EET),Open,High,Low,Close,Volume
2020.01.09 01:00:00,1557.152,1557.452,1555.202,1555.302,0.045
```

关键口径：

- `time_col = "Time (EET)"`
- `source_tz = "Europe/Helsinki"`
- `timestamp_is_bar_open = True` 表示 MT4/MT5 row time 是 candle open time，项目内部转为 close time。
- 若数据源已经是 close time，必须先改配置，不能在训练脚本里硬补。

## Config Contract

常用配置 owner：`config.py`。

| Area | Fields |
|------|--------|
| Data | `csv_path`, `time_col`, `source_tz`, `timestamp_is_bar_open` |
| Timeframes | `execution_timeframe`, `decision_timeframe` |
| Split | `train_frac`, `val_frac`, `test_frac`, `split_embargo_bars` |
| Sliding WF | `sliding_train_years`, `sliding_val_months`, `sliding_test_months`, `sliding_step_months` |
| Costs | `spread_price`, `slippage_price`, `commission_per_trade` |
| Risk/reward | `risk_fraction`, `holding_penalty`, `reward_mtm_weight` |
| PPO | `ppo_learning_rate`, `ppo_ent_coef`, `ppo_n_epochs`, `ppo_clip_range`, `ppo_target_kl`, `ppo_weight_decay`, `ppo_net_arch` |

## Action Contract

RL agent action space is bracket-based:

```text
MultiDiscrete([direction, SL bucket, TP/R bucket])
direction: 0 = flat/close, 1 = long, 2 = short
SL bucket: CFG.sl_atr_multipliers
TP bucket: CFG.tp_r_multipliers
```

The agent controls direction and bracket shape, not position sizing. Position size is fixed-fractional risk based.

## Validation Artifacts

`run_pipeline.py` writes validation/pretest artifacts under `outputs/`:

```text
outputs/policy_search.csv
outputs/selected_policy.csv
outputs/performance_report.csv
outputs/selected_val_trade_log.csv
outputs/selected_val_equity_curve.csv
outputs/walk_forward_baseline.csv
outputs/01_val_candles_indicators.html
outputs/04_val_trades_on_chart.html
outputs/05_val_equity_drawdown.html
```

These are iteration artifacts, not final sealed-holdout evidence.

## RL Walk-forward Artifacts

`train_ppo.py` writes RL artifacts under `models/`:

```text
models/sliding/fold_*/
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/best_model/best_model.zip
models/best_model/best_model_vecnorm.pkl
models/run_info.json
models/NO_DEPLOY.txt
```

If `models/NO_DEPLOY.txt` exists, treat the run as research-only unless later evidence explicitly changes that status.

## Holdout Artifacts

`final_holdout_eval.py` writes one-time sealed holdout artifacts:

```text
outputs/final_holdout/holdout_report.csv
outputs/final_holdout/rl_test_trade_log.csv
outputs/final_holdout/rl_test_equity_curve.csv
```

Do not use these to iterate on parameters after reveal.
