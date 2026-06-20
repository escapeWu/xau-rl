# Research and Development Loop

> 上级：[`README.md`](README.md)

本文件定义本项目长期运行的 lightweight R&D loop。它借鉴 RD-Agent 的“Research -> Development -> Validation -> Feedback”闭环，但保持本项目轻量：不引入外部 RD-Agent 运行时，不创建 taskBoard，不把 sealed holdout 放入日常迭代。

## Core Loop

```text
R0 Specification
  -> R1 Hypothesis
  -> R2 Experiment Plan
  -> R3 Development
  -> R4 Validation
  -> R5 Feedback
  -> R6 Memory
  -> next hypothesis

Final only: frozen candidate -> sealed holdout
```

## R0 Specification

每轮实验前先声明并冻结规格：

- data file / date range
- `source_tz`, `timestamp_is_bar_open`
- `execution_timeframe`, `decision_timeframe`
- spread, slippage, commission
- split / walk-forward settings
- feature set
- reward settings
- bracket action space
- PPO key parameters
- evaluation metrics and artifacts

若本轮修改了以上多个方向，必须说明原因；默认一轮实验只改一个主要变量。

## R1 Hypothesis

实验必须先有可验证假设。例如：

```text
当前 PPO 在 train 表现较好但 OOS 不稳定，可能是 policy 过早收敛。
提高 entropy、减少 n_epochs 可能改善 walk-forward 一致性。
```

不要执行没有假设的“随手试试”。

## R2 Experiment Plan

使用 [`experiment-template.md`](experiment-template.md) 记录：

- hypothesis
- changed owner files
- frozen settings
- validation plan
- expected artifacts
- holdout status

每个实验必须明确是否允许触碰 holdout。默认不允许。

## R3 Development

只修改 owning files：

| Direction | Owner |
|-----------|-------|
| data / timeframe / costs / PPO config | `config.py` |
| data loading / timezone / split | `data_loader.py` |
| features | `features.py` |
| reward / bracket / M1 execution | `env_bracket.py` |
| baseline | `baselines.py`, `run_pipeline.py` |
| PPO / checkpoint / gate | `train_ppo.py` |
| metrics | `evaluate.py` |
| charts | `visualize.py`, `view_results.py` |
| sealed holdout | `final_holdout_eval.py` |

不要创建平行实现；新增逻辑前先定向搜索 owner。

## R4 Validation

推荐验证顺序：

```bash
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
python run_pipeline.py
python train_ppo.py
```

`python final_holdout_eval.py` 只在 frozen candidate 后运行一次，不属于日常 loop。

## R5 Feedback

反馈必须基于 artifacts，而不是主观判断。至少检查：

- fold-level return
- max drawdown
- profit factor
- Sharpe-like
- `n_trades`
- stitched OOS equity
- `models/NO_DEPLOY.txt`

结论只能是：

```text
accept / reject / inconclusive
```

`inconclusive` 的常见原因：交易太少、fold 不一致、成本不可信、收益由少数交易贡献。

## R6 Memory

- 单次实验索引写入 [`experiment-ledger.md`](experiment-ledger.md)。
- 稳定设计决策写入 [`decisions.md`](decisions.md)。
- 跨项目长期经验写入 [`../../reference/project-memory.md`](../../reference/project-memory.md)。
- 原始结果保留在 `outputs/` 与 `models/`；不要把完整指标搬进 docs。

## Holdout Rule

日常 R&D loop 不包含 sealed holdout。只有当满足以下条件时才进入 holdout：

1. pipeline 正常；
2. baseline sanity 通过；
3. PPO walk-forward 已评估；
4. consistency gate 状态明确；
5. 模型、配置和评估口径冻结；
6. 不再根据 holdout 调参。

如果 holdout 被用于迭代，必须停止并标记 holdout 污染风险。
