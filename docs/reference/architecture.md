# Architecture Reference

> 上级：[`INDEX.md`](INDEX.md)

本文件记录当前项目的稳定架构事实和 owner 边界。详细训练教程见 [`../USAGE_ZH.md`](../USAGE_ZH.md)，RL training skill 见 [`.agent/skills/rl-trading-training/`](../../.agent/skills/rl-trading-training/SKILL.md)。

## System Shape

```text
XAUUSD M1 CSV
  -> data_loader.py
  -> features.py
  -> env_bracket.py
  -> baselines.py / train_ppo.py
  -> evaluate.py
  -> visualize.py / view_results.py
  -> outputs/ and models/
```

## Layer Responsibilities

| Layer | Owner files | Responsibility |
|-------|-------------|----------------|
| Configuration | `config.py` | 数据路径、timeframe、split、成本、风控、PPO、gate 参数 |
| Data loading | `data_loader.py` | CSV 读取、broker timezone、bar open/close、OHLCV 清洗、resample、split/fold |
| Features | `features.py` | 因果 observation features、ATR/price-normalized 特征、warmup |
| Trading env | `env_bracket.py` | Gymnasium env、MultiDiscrete bracket action、reward、M1 TP/SL 执行模拟 |
| Baseline | `baselines.py`, `run_pipeline.py` | baseline 搜索、validation-only smoke test、pre-RL 产物 |
| RL training | `train_ppo.py` | PPO 训练、VecNormalize、checkpoint selection、walk-forward、consistency gate |
| Evaluation | `evaluate.py` | equity/trade summary、drawdown、Sharpe-like、PF 等指标 |
| Visualization | `visualize.py`, `view_results.py` | Plotly 图表、任意切片查看、HTML 输出 |
| Holdout | `final_holdout_eval.py` | 模型冻结后的 sealed holdout 一次性揭盲 |

## Research Flow

```text
G0 setup
  data file exists; config is credible
        v
G1 pipeline
  run_pipeline.py passes; validation artifacts exist
        v
G2 baseline sanity
  baseline trade log and charts are plausible
        v
G3 PPO walk-forward
  train_ppo.py produces fold-level OOS evidence
        v
G4 consistency gate
  fold consistency, PF, DD, Sharpe-like and NO_DEPLOY status are known
        v
G5 frozen holdout
  final_holdout_eval.py runs once after model/config freeze
```

## Important Boundaries

- M1 is the execution layer; decision bars are higher timeframe observations.
- Features must be causal: each timestamp may use only completed current/past bars.
- When TP and SL are both hit inside one M1 candle, the simulator uses the conservative SL-first assumption.
- `outputs/` and `models/` are evidence, not source truth. Source truth is current code and config.
- `final_holdout_eval.py` is not an iterative tuning tool.

## Owner Search Recipes

Use targeted search before adding new logic:

```bash
rg -n "timestamp_is_bar_open|source_tz|resample|split_train_val_test|make_sliding" data_loader.py train_ppo.py config.py
rg -n "reward|holding_penalty|sl_atr|tp_r|MultiDiscrete" env_bracket.py config.py
rg -n "NO_DEPLOY|gate_|sliding_|VecNormalize|checkpoint" train_ppo.py config.py model_artifacts.py
rg -n "plot_|write_html|view_slice|selected_val|holdout" visualize.py view_results.py run_pipeline.py final_holdout_eval.py
```
