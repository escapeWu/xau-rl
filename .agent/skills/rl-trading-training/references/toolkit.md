# 工具与脚本参考

本参考列出本 skill 推荐使用的项目脚本、产物和辅助检查工具。

## 项目脚本

### `run_pipeline.py`

用途：数据、特征、baseline、validation 图表 smoke test。

命令：

```bash
python run_pipeline.py
```

先跑它，再训练 PPO。

### `train_ppo.py`

用途：训练 PPO bracket-trading agent，默认走 sliding-window walk-forward。

命令：

```bash
python train_ppo.py
```

重点产物：

```text
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/best_model/best_model.zip
models/best_model/best_model_vecnorm.pkl
models/NO_DEPLOY.txt
```

### `final_holdout_eval.py`

用途：最终 sealed holdout 揭盲。

命令：

```bash
python final_holdout_eval.py
```

只在模型冻结后运行，不要用于反复调参。

### `view_results.py`

用途：从已保存 trade/equity CSV 生成切片图表。

命令：

```bash
python view_results.py --bars 1000
python view_results.py --start 2024-01-01 --end 2024-06-01
python view_results.py --split val --no-browser
```

### `training_diagnostics.py`

用途：查看训练诊断和 walk-forward 摘要。若用户问“训练过程中发生了什么”，优先检查该脚本和相关输出。

## Skill 辅助脚本

### `scripts/rl_trading_doctor.py`

用途：轻量检查当前仓库是否具备训练/评估所需的关键配置和产物。

命令：

```bash
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
```

它不会训练模型，也不会读取 sealed holdout 结果做调参建议。它只报告：

- 关键源码文件是否存在。
- 数据路径是否存在。
- 主要配置值。
- validation、walk-forward、holdout 产物是否存在。
- 是否有 `models/NO_DEPLOY.txt`。
- 若 CSV 可读，输出关键指标和交易数量摘要。

## 建议回答模板

当用户问“下一步怎么训练/看结果”，按这个结构回答：

```text
1. 当前阶段：pipeline / PPO walk-forward / holdout。
2. 应运行的命令：...
3. 应检查的文件：...
4. 判断标准：n_trades、PF、DD、OOS 一致性、NO_DEPLOY。
5. 下一步：修数据/调成本/调 reward/调 PPO 正则化/冻结模型后 holdout。
```

## 修改代码时的安全原则

- 不要为了图表或诊断修改训练逻辑。
- 不要在同一次实验里同时改特征、reward、成本和 PPO 参数。
- 改 `config.py` 后，把关键配置记录到结果说明里。
- 使用 holdout 后，不要再根据 holdout 继续调参。
