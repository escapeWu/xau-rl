# Training Workflow

> 上级：[`README.md`](README.md)

本文件整理本项目 RL for Trading 的稳定训练流程。更细的 agent 操作提示见 [`.agent/skills/rl-trading-training/references/training-workflow.md`](../../../.agent/skills/rl-trading-training/references/training-workflow.md)。

## Training Objective

本项目训练的是 XAUUSD PPO bracket-trading agent：

- M1 candles 是执行层，用于 TP/SL intrabar 模拟。
- 决策层默认是 H1，agent 每根决策 bar 观察一次并行动一次。
- 动作空间是 `MultiDiscrete([direction, SL bucket, TP/R bucket])`。
- direction: `0 = flat/close`, `1 = long`, `2 = short`。
- SL bucket 来自 `CFG.sl_atr_multipliers`。
- TP/R bucket 来自 `CFG.tp_r_multipliers`。

## Recommended Sequence

不要直接从 PPO 开始。推荐顺序：

```bash
pip install -r requirements.txt
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
python run_pipeline.py
python train_ppo.py
python final_holdout_eval.py
```

实际研究时，`final_holdout_eval.py` 只在模型、配置和评估口径冻结后运行一次。

## Stage Gates

```text
G0 setup
  config 可加载；数据路径、时区、timestamp、成本口径明确
        v
G1 pipeline
  run_pipeline.py 完成；validation-only 报告、trade log、equity、HTML 图可读
        v
G2 baseline sanity
  baseline 行为可解释；没有明显时间错位、交易过少或成本失真
        v
G3 PPO walk-forward
  train_ppo.py 完成；fold-level OOS 结果和 stitched OOS equity 可读
        v
G4 consistency gate
  fold 一致性、PF、DD、Sharpe-like、NO_DEPLOY 状态明确
        v
G5 frozen holdout
  final_holdout_eval.py 在冻结后揭盲一次
```

不要从 G0 直接跳到 G3/G5。

## Tuning Priority

每次实验只改一个主要方向。

1. **Data and costs**：`config.py` 中的 `csv_path`, `source_tz`, `timestamp_is_bar_open`, `spread_price`, `slippage_price`, `commission_per_trade`。
2. **Bracket space**：`sl_atr_multipliers`, `tp_r_multipliers`。
3. **Reward shaping**：`holding_penalty`, `reward_mtm_weight`, `risk_fraction`，实际实现 owner 是 `env_bracket.py` 和 `config.py`。
4. **PPO regularization**：`ppo_learning_rate`, `ppo_ent_coef`, `ppo_n_epochs`, `ppo_clip_range`, `ppo_target_kl`, `ppo_weight_decay`, `ppo_net_arch`。

## Result Reading

训练结束后至少检查：

- `models/sliding_walk_forward_summary.csv`
- `models/sliding_oos_equity.csv`
- `models/best_model/best_model.zip`
- `models/best_model/best_model_vecnorm.pkl`
- `models/NO_DEPLOY.txt`

若存在 `NO_DEPLOY.txt`，该 run 只能按 research-only 表述。
