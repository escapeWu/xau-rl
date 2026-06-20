# Runbook and Testing Reference

> 上级：[`INDEX.md`](INDEX.md)

本文件记录本项目的运行、验证和 harness 初始化自检步骤。PPO 训练可能很重，除非任务需要，不要为了文档变更运行完整训练。

## Environment Setup

```bash
pip install -r requirements.txt
```

准备默认数据文件，路径见 `config.py`：

```text
data/XAUUSD_1 Min_Bid_2003.05.05_2026.05.31.csv
```

## Skill Doctor

轻量检查 `.agent` skill、关键源码、配置和产物状态：

```bash
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
```

脚本只读，不训练模型，也不修改产物。

## Pipeline Smoke Test

第一次复现或改数据/特征/成本后，先跑：

```bash
python run_pipeline.py
```

通过条件：

- 数据读取和时间戳处理无报错。
- validation-only baseline 产物写入 `outputs/`。
- 交易图和 equity/drawdown 图可打开。
- 没有明显 feature leakage 或时间错位迹象。

## PPO Walk-forward

pipeline 可信后再跑：

```bash
python train_ppo.py
```

重点查看：

```text
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/NO_DEPLOY.txt
```

不要只看最后 checkpoint 或单个 fold。

## Holdout Reveal

只在模型和配置冻结后运行一次：

```bash
python final_holdout_eval.py
```

如果根据 holdout 继续调参，holdout 就不再是 sealed holdout。

## Visualization

查看已保存切片：

```bash
python view_results.py --bars 1000
python view_results.py --start 2024-01-01 --end 2024-06-01
python view_results.py --split val --no-browser
```

默认读取 validation artifacts。查看 holdout 时必须显式传入 holdout trade/equity 文件，并确认模型已经冻结。

## Harness Navigation Checklist

- Start at `AGENTS.md`.
- Reach `docs/OVERVIEW.md`.
- Reach `docs/feature/INDEX.md` and `docs/reference/INDEX.md`.
- Reach `docs/feature/rl-trading-research/README.md`.
- Reach `docs/feature/rl-trading-research/requirements.md` when expected behavior matters.
- Walk back through each file's `> 上级` link.
- Confirm active docs are not mixed into `docs/archive/`.
- Confirm no `.cursor` skill/rule path is required for this setup.

## Script Syntax Check

After changing the doctor script:

```bash
python -c "import ast, pathlib; ast.parse(pathlib.Path('.agent/skills/rl-trading-training/scripts/rl_trading_doctor.py').read_text(encoding='utf-8')); print('syntax OK')"
```
