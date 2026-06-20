# XAUUSD RL Trading Research Overview

> 上级：[`../AGENTS.md`](../AGENTS.md)

本项目是一个面向 XAUUSD M1 数据的强化学习交易研究框架。它用 M1 作为执行层，在更高决策周期上训练 PPO bracket-trading agent，并通过 baseline、walk-forward 和 sealed holdout 管理研究可信度。

## 项目地图

| 路径 | 用途 |
|------|------|
| [`feature/INDEX.md`](feature/INDEX.md) | 研究/功能模块入口 |
| [`reference/INDEX.md`](reference/INDEX.md) | 架构、产物契约、运行验证等稳定参考 |
| [`archive/INDEX.md`](archive/INDEX.md) | 历史材料入口，默认不读 |
| [`USAGE_ZH.md`](USAGE_ZH.md) | 中文长说明和复现实验说明 |

## 核心研究模块

- [`feature/rl-trading-research/`](feature/rl-trading-research/README.md)：XAUUSD RL bracket-trading 训练、评估、图表和产物路由。

## 核心链路

```text
XAUUSD M1 CSV
  -> 时间戳/时区清洗
  -> M1 执行层保留
  -> 决策周期重采样
  -> 因果特征
  -> train/val/test 或 sliding walk-forward
  -> baseline / PPO
  -> BracketTradingEnv
  -> 回测评估
  -> outputs/ 与 models/
```

## 读取规则

1. 先读本文件确认项目入口。
2. 需要训练/评估细节时进入 [`feature/rl-trading-research/README.md`](feature/rl-trading-research/README.md)。
3. 需要架构、产物契约或运行命令时进入 [`reference/INDEX.md`](reference/INDEX.md)。
4. 需要完整中文教程时再读 [`USAGE_ZH.md`](USAGE_ZH.md)。

不要一次性全量读取 docs；按任务只读取相关 leaf 文档。
