# RL Trading Research Decisions

> 上级：[`README.md`](README.md)

本文件记录 RL trading research 模块的稳定设计决策。它不同于 [`experiment-ledger.md`](experiment-ledger.md)：ledger 记录单次实验索引，decisions 只记录跨实验仍然成立的设计选择。

## Decision Log

| Date | Decision | Reason | Impact | Superseded when |
|------|----------|--------|--------|-----------------|
| 2026-06-21 | M1 保留为执行层 | 决策周期 K 线无法判断 TP/SL intrabar 先后顺序 | `env_bracket.py` 使用 M1 candles 模拟 bracket execution | 有可靠 tick-level execution simulator |
| 2026-06-21 | 同一根 M1 candle 同时触及 TP 和 SL 时按 SL first | 保守处理无法判定的触发顺序 | 降低乐观回测风险 | 有数据能证明真实先后顺序 |
| 2026-06-21 | sealed holdout 只在模型冻结后揭盲一次 | 防止 holdout 退化为 validation | `final_holdout_eval.py` 不进入日常 R&D loop | 重新定义新的未触碰 holdout 数据集 |
| 2026-06-21 | 训练结论优先看 sliding walk-forward OOS | 单次 split 容易被行情 regime 偶然性影响 | `models/sliding_*` 是日常 RL 评估主证据 | 项目改用更强的时间序列 OOS 协议 |
| 2026-06-21 | `models/NO_DEPLOY.txt` 存在时按 research-only 表述 | consistency gate 未通过时不能包装为可部署策略 | 输出回答必须说明 gate 状态 | gate 规则更新且新的 run 明确通过 |
| 2026-06-21 | observation 特征优先 ATR/price-normalized 或比例类 | XAUUSD 跨年份价格尺度变化明显 | 新特征优先放 `features.py` 并保持因果性 | 有充分 OOS 证据支持其他稳定表达 |
| 2026-06-21 | 使用 `.agent` 作为 repo-local skill/harness 目录 | 避免绑定到 Cursor 专用目录 | skill 和 harness 文档引用 `.agent/skills/...` | 项目明确迁移到其他统一约定 |

## Decision Promotion Rule

只有满足以下条件时，单次实验结论才能从 ledger 晋升为 decision：

1. 有明确 hypothesis 和 validation artifact。
2. 不是 sealed holdout 调参产物。
3. 结论跨多个 fold 或多次实验仍然成立。
4. 对代码 owner、评估协议或研究边界有长期影响。
5. 已说明 superseded 条件。

## Non-decisions

以下内容不要写入本文件：

- 单次 run 的完整指标。
- 尚未验证的猜测。
- 临时 notebook 观察。
- 根据 sealed holdout 反复调参得到的结论。
