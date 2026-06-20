# Toolkit and Scripts

> 上级：[`README.md`](README.md)

本文件整理本项目训练、诊断、回测和可视化脚本的稳定工具清单。更细的 agent 操作提示见 [`.agent/skills/rl-trading-training/references/toolkit.md`](../../../.agent/skills/rl-trading-training/references/toolkit.md)。

## Core Commands

| Command | Stage | Purpose |
|---------|-------|---------|
| `python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py` | G0/G1 | 轻量检查源码、配置、数据路径和产物状态 |
| `python run_pipeline.py` | G1/G2 | 数据、特征、baseline、validation 图表 smoke test |
| `python train_ppo.py` | G3/G4 | PPO sliding walk-forward 训练与 OOS 评估 |
| `python final_holdout_eval.py` | G5 | 模型冻结后 sealed holdout 一次性揭盲 |
| `python view_results.py --bars 1000` | Visualization | 查看已保存 trade/equity 的图表切片 |

## Project Script Roles

| Script | Role |
|--------|------|
| `config.py` | 数据、timeframe、成本、risk、PPO、gate 配置 owner |
| `data_loader.py` | CSV、timezone、bar open/close、resample、split/fold owner |
| `features.py` | 因果 observation features owner |
| `env_bracket.py` | bracket env、reward、M1 TP/SL 执行模拟 owner |
| `baselines.py` | random / EMA-ATR baseline owner |
| `run_pipeline.py` | pre-RL validation pipeline owner |
| `train_ppo.py` | PPO、checkpoint、VecNormalize、walk-forward、gate owner |
| `evaluate.py` | 指标、drawdown、trade summary owner |
| `visualize.py` / `view_results.py` | 图表和切片查看 owner |
| `final_holdout_eval.py` | sealed holdout owner |

## Artifact Map

| Artifact | Produced by | Meaning |
|----------|-------------|---------|
| `outputs/performance_report.csv` | `run_pipeline.py` | validation-only baseline/report summary |
| `outputs/selected_val_trade_log.csv` | `run_pipeline.py` | validation trade log |
| `outputs/selected_val_equity_curve.csv` | `run_pipeline.py` | validation equity curve |
| `outputs/01_*.html` to `outputs/05_*.html` | `run_pipeline.py` | validation/pretest charts |
| `models/sliding_walk_forward_summary.csv` | `train_ppo.py` | fold-level OOS summary |
| `models/sliding_oos_equity.csv` | `train_ppo.py` | stitched OOS equity |
| `models/best_model/best_model.zip` | `train_ppo.py` | selected PPO checkpoint |
| `models/best_model/best_model_vecnorm.pkl` | `train_ppo.py` | matching VecNormalize state |
| `models/NO_DEPLOY.txt` | `train_ppo.py` gate | deployment gate failed / research-only marker |
| `outputs/final_holdout/holdout_report.csv` | `final_holdout_eval.py` | frozen holdout report |

## Safe Answer Template

回答“下一步怎么训练/怎么看结果”时使用：

```text
当前阶段：G0/G1/G2/G3/G4/G5
证据来源：config / outputs / models / holdout artifact
应运行命令：...
应检查文件：...
判断标准：n_trades、PF、DD、OOS 一致性、NO_DEPLOY
下一步：修数据 / 调成本 / 调 reward / 调 PPO 正则化 / 冻结后 holdout
```

## Safety Rules

- Doctor 脚本只诊断，不训练、不调参、不修改产物。
- 不要为了图表或诊断修改训练逻辑。
- 不要一次实验同时改特征、reward、成本和 PPO 参数。
- 改 `config.py` 后，记录关键配置变化。
- 使用 holdout 后，不要再根据 holdout 继续调参。
