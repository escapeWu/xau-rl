# RL Trading Research Requirements

> 上级：[`README.md`](README.md)

本文件记录本研究模块的 expected behavior、验收口径、边界和非目标。当前实现状态见 [`README.md`](README.md)。

## Goals

- 使用 XAUUSD M1 数据建立可复现实验链路。
- 保留 M1 执行层，用高周期决策层训练 PPO bracket-trading agent。
- 使用因果、平稳、ATR/price-normalized 或比例类特征，避免直接喂绝对价格。
- 通过 baseline、sliding walk-forward 和 sealed holdout 区分 research evidence 与 deployable evidence。
- 输出可检查的报告、trade log、equity curve 和 HTML 图表。

## Acceptance Criteria

### G0 Setup

- `config.py` 可加载。
- 默认或指定 CSV 路径存在。
- `source_tz`, `timestamp_is_bar_open`, `execution_timeframe`, `decision_timeframe` 与数据源口径一致。
- 交易成本假设明确：spread、slippage、commission。

### G1 Pipeline

- `python run_pipeline.py` 能完成数据读取、特征构造、baseline 搜索和 validation-only 输出。
- `outputs/performance_report.csv`、trade log、equity curve 和关键 HTML 图表可读。
- 图表不显示明显时间错位或未来函数迹象。

### G2 Baseline Sanity

- baseline 交易行为可解释。
- 交易数量、持仓时间、PF、DD 不表现为明显统计幻觉。
- baseline 与 RL 结论必须在同一 split/window 语境下比较。

### G3 PPO Walk-forward

- `python train_ppo.py` 产出 fold-level OOS 结果。
- `models/sliding_walk_forward_summary.csv` 和 `models/sliding_oos_equity.csv` 可用于解释跨时期稳定性。
- 不使用最后 checkpoint 代替 best checkpoint selection。

### G4 Consistency Gate

- 明确 `models/NO_DEPLOY.txt` 是否存在。
- 检查 fold 一致性、profit factor、max drawdown、Sharpe-like、n_trades。
- 如果 gate 未通过，只能表述为 research-only。

### G5 Frozen Holdout

- 模型、配置和评估口径冻结后才运行 `python final_holdout_eval.py`。
- Holdout 只揭盲一次；揭盲后不能再用于调参循环。

## Non-goals

- 不承诺稳定盈利或可实盘部署。
- 不处理真实下单、broker API、资金划转或账户凭据。
- 不把 sealed holdout 当 validation 使用。
- 不为了漂亮曲线降低真实交易成本假设。
- 不用 taskBoard / tasks WIP 机制初始化本项目；本项目使用轻量 stage gates。

## Research Risks

- 时间戳 open/close 错位会造成决策与成交错位。
- 成本设置过于乐观会显著夸大短线黄金策略表现。
- 交易次数太少时，PF、win rate、return 都不稳定。
- 单个 fold 暴赚不等于跨时期 edge。
- 新增特征若不保持因果性，会造成未来函数。

## Evidence Rules

- 结论必须说明来自 validation、sliding walk-forward OOS 还是 sealed holdout。
- 报告结论必须引用具体 artifact 或配置来源。
- 文档是导航和口径；当前代码、配置和运行产物是事实来源。
