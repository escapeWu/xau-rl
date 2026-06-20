# RL for Trading 训练工作流

本参考用于回答“如何训练 RL for Trading agent”“推荐训练顺序”“该改哪些参数”等问题。入口文件只负责索引；这里记录实际训练流程。

## 项目训练目标

本项目训练的是 XAUUSD bracket-trading PPO agent：

- 执行层：M1 candles，用于模拟 TP/SL 触发顺序。
- 决策层：默认 H1，agent 每根决策 bar 观察一次并行动一次。
- 动作空间：`MultiDiscrete([direction, SL bucket, TP/R bucket])`。
- 方向：`0 = flat/close`, `1 = long`, `2 = short`。
- SL：从 `CFG.sl_atr_multipliers` 选择 ATR 倍数。
- TP：从 `CFG.tp_r_multipliers` 选择 R 倍数。

## 推荐训练顺序

不要直接从 PPO 开始。按下面顺序推进：

```bash
pip install -r requirements.txt
python run_pipeline.py
python train_ppo.py
python final_holdout_eval.py
```

实际研究时，`final_holdout_eval.py` 只在模型冻结后运行一次；不要把 holdout 当 validation 使用。

### 1. 数据与 pipeline smoke test

先运行：

```bash
python run_pipeline.py
```

确认以下环节正常：

- CSV 路径、列名、时间戳解析正确。
- M1 数据能重采样到 `CFG.decision_timeframe`。
- 特征构造没有明显泄漏或 NaN/inf 问题。
- baseline 能在 train/val 上完成搜索。
- validation-only 图表和报告写入 `outputs/`。

重点检查：

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

如果这一步失败，不要继续训练 PPO；先修数据、时间戳、特征或成本配置。

### 2. PPO walk-forward 训练

默认运行：

```bash
python train_ppo.py
```

当前项目默认使用 sliding-window walk-forward：

```text
最近 5 年训练
接下来 6 个月 validation 选 checkpoint
再后 6 个月 OOS test 评估
窗口向前滑 6 个月
重复直到历史结束
```

相关配置位于 `config.py`：

```python
sliding_train_years = 5.0
sliding_val_months = 6
sliding_test_months = 6
sliding_step_months = 6
```

常见训练输出：

```text
models/sliding/fold_*/
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/best_model/best_model.zip
models/best_model/best_model_vecnorm.pkl
models/run_info.json
models/NO_DEPLOY.txt
```

如果出现 `models/NO_DEPLOY.txt`，说明策略没有通过 consistency gate。可以继续研究，但不要描述为可部署策略。

### 3. Sealed holdout 揭盲

只在以下条件满足后运行：

- pipeline 和 baseline 已检查。
- PPO walk-forward 结果已评估。
- 模型、配置、训练方式已经冻结。
- 不再根据 holdout 结果继续调参。

运行：

```bash
python final_holdout_eval.py
```

输出：

```text
outputs/final_holdout/rl_test_equity_curve.csv
outputs/final_holdout/rl_test_trade_log.csv
outputs/final_holdout/holdout_report.csv
```

## 推荐调参顺序

每次只改一个方向，否则结果难以解释。

### 优先级 1：数据与成本

文件：`config.py`

```python
csv_path
source_tz
spread_price
slippage_price
commission_per_trade
risk_fraction
```

先确认时间戳和成本假设可信，再讨论模型表现。

### 优先级 2：bracket 空间

文件：`config.py`

```python
sl_atr_multipliers
tp_r_multipliers
```

空间太小会限制策略，空间太大则更难训练。建议先保持少量离散 bucket，再逐步扩展。

### 优先级 3：reward shaping

文件：`env_bracket.py`, `config.py`

```python
holding_penalty
reward_mtm_weight
risk_fraction
```

reward 默认按风险预算归一化，而不是直接使用现金 PnL。修改 reward 后要重新看交易频率、持仓时间、avg R 和回撤。

### 优先级 4：PPO 正则化

文件：`config.py`, `train_ppo.py`

```python
ppo_learning_rate
ppo_ent_coef
ppo_n_epochs
ppo_clip_range
ppo_target_kl
ppo_weight_decay
ppo_net_arch
```

当 train 很好、validation/OOS 崩掉时，优先：

- 降低 learning rate。
- 减少 `ppo_n_epochs`。
- 增加 entropy 或 weight decay。
- 保持 tight clip range。
- 使用 checkpoint selection，不要直接用最后 checkpoint。

## 训练结果判读

训练结束后至少检查：

- 每个 fold 的 return、profit factor、max drawdown、n_trades。
- 拼接后的 OOS equity：`models/sliding_oos_equity.csv`。
- gate 是否通过：是否存在 `models/NO_DEPLOY.txt`。
- best model 是否带有匹配的 VecNormalize：`best_model_vecnorm.pkl`。

不要只看 `total_return_pct`。RL 交易训练更看重跨时期一致性，而不是单次漂亮收益曲线。
