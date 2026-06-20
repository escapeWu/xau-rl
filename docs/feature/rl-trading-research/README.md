# RL Trading Research

> 上级：[`../INDEX.md`](../INDEX.md)

本模块记录当前 XAUUSD RL bracket-trading 研究框架的实现状态、入口脚本和运行产物路由。预期行为、验收口径和非目标见 [`requirements.md`](requirements.md)。

## Current Implementation

本项目以 MT4/MT5 风格 XAUUSD M1 CSV 为输入：

1. `data_loader.py` 读取、清洗、时区处理并保留 M1 执行层。
2. `features.py` 在决策周期上构造因果、平稳、ATR/price-normalized observation features。
3. `env_bracket.py` 提供 Gymnasium `BracketTradingEnv`，用 M1 candles 模拟 TP/SL 触发顺序。
4. `run_pipeline.py` 运行数据/特征/baseline/validation 图表 smoke test。
5. `train_ppo.py` 训练 PPO agent，并通过 sliding walk-forward 检查 OOS 稳定性。
6. `final_holdout_eval.py` 在模型冻结后揭盲 sealed holdout。

## Main Commands

```bash
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
python run_pipeline.py
python train_ppo.py
python final_holdout_eval.py
```

不要跳过 `run_pipeline.py` 直接跑 PPO；不要在模型未冻结时反复运行 `final_holdout_eval.py`。

## Artifact Routing

| Stage | Main files | Purpose |
|-------|------------|---------|
| Pipeline / baseline | `outputs/performance_report.csv`, `outputs/selected_val_trade_log.csv`, `outputs/selected_val_equity_curve.csv` | validation-only sanity evidence |
| Pipeline charts | `outputs/01_*.html` through `outputs/05_*.html` | 数据、特征、交易和权益图检查 |
| RL walk-forward | `models/sliding_walk_forward_summary.csv`, `models/sliding_oos_equity.csv` | 多折 OOS 稳定性证据 |
| Deployment gate | `models/NO_DEPLOY.txt` | 存在则视为 research-only |
| Best model | `models/best_model/best_model.zip`, `models/best_model/best_model_vecnorm.pkl` | checkpoint 与 VecNormalize 成对保存 |
| Sealed holdout | `outputs/final_holdout/holdout_report.csv`, `outputs/final_holdout/rl_test_trade_log.csv`, `outputs/final_holdout/rl_test_equity_curve.csv` | 冻结后一次性揭盲 |

## Reading Routes

- 快速复现和长说明：[`../../USAGE_ZH.md`](../../USAGE_ZH.md)
- 架构与 owner 边界：[`../../reference/architecture.md`](../../reference/architecture.md)
- 数据/配置/产物契约：[`../../reference/interfaces.md`](../../reference/interfaces.md)
- 运行验证步骤：[`../../reference/runbook-testing.md`](../../reference/runbook-testing.md)
- RL training skill：[`../../../.agent/skills/rl-trading-training/SKILL.md`](../../../.agent/skills/rl-trading-training/SKILL.md)

## Topic Guides

| Topic | File | Use when |
|-------|------|----------|
| Training workflow | [`training-workflow.md`](training-workflow.md) | 需要训练顺序、stage gates、调参优先级 |
| Backtesting and evaluation | [`backtesting-evaluation.md`](backtesting-evaluation.md) | 需要区分 validation、walk-forward OOS、sealed holdout 或解释指标 |
| Chart visualization | [`chart-visualization.md`](chart-visualization.md) | 需要生成、查看或解释图表 |
| Pitfalls and debugging | [`pitfalls.md`](pitfalls.md) | 训练不稳定、结果异常、时间错位、成本/holdout 风险排查 |
| Toolkit and scripts | [`toolkit.md`](toolkit.md) | 需要命令、脚本职责、产物路由或回答模板 |
| Research loop | [`research-loop.md`](research-loop.md) | 需要按 hypothesis -> experiment -> feedback 长期运行研究 |
| Experiment template | [`experiment-template.md`](experiment-template.md) | 开始一轮受控实验前复制/填写实验卡 |
| Experiment ledger | [`experiment-ledger.md`](experiment-ledger.md) | 查找或登记历史实验索引、artifact 和结论 |
| Design decisions | [`decisions.md`](decisions.md) | 查看跨实验仍成立的稳定研究决策 |

## Stage Gates

```text
G0 setup -> G1 pipeline -> G2 baseline sanity -> G3 PPO walk-forward -> G4 consistency gate -> G5 frozen holdout
```

回答训练/评估问题时必须说明当前处于哪一 gate，以及下一 gate 的准入条件。

## Documentation Ownership

- 当前实现状态和产物路由更新到本 README。
- expected behavior、验收口径、非目标更新到 `requirements.md`。
- 长期架构和契约更新到 `docs/reference/`。
- 单次实验结果不要写入本文件；保留在 `outputs/`、`models/` 或必要时归档。
