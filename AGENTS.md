# Agent 开发规约

> 项目上下文入口：[`docs/OVERVIEW.md`](docs/OVERVIEW.md)

本仓库是一个 XAUUSD 强化学习交易研究项目。Agent 开始任何非 trivial 分析、训练、回测、可视化或代码修改前，先按本文档的渐进式披露规则定位上下文。禁止把密钥、凭证、私有数据、broker 账户信息或真实交易凭据写入 docs、日志或用户可见输出。

## 核心原则

- **Research-first**：本项目默认是研究框架，不把单次回测结果表述为可部署收益承诺。
- **Evidence-first**：先看配置、代码、产物、图表和 fold 指标，再给结论。
- **Sealed holdout discipline**：`final_holdout_eval.py` 只在模型冻结后揭盲一次，不能当 validation 反复调参。
- **Causal features only**：特征只能使用当前及过去已经完成的 bar，禁止未来函数。
- **Costs are part of truth**：spread、slippage、commission 不可信时，任何收益曲线都不能当真。

## 分层约束

项目核心层次如下：

```text
raw M1 CSV
  -> data_loader.py          # 时间戳、时区、清洗、重采样、split/fold
  -> features.py             # 因果、平稳、ATR/price-normalized 特征
  -> env_bracket.py          # bracket trading 环境、reward、M1 TP/SL 执行模拟
  -> baselines.py            # baseline 策略
  -> train_ppo.py            # PPO、walk-forward、checkpoint/gate
  -> evaluate.py             # 指标、drawdown、trade summary
  -> visualize.py/view_results.py
  -> outputs/ and models/    # 运行产物
```

不要把特征、reward、评估、可视化逻辑混在同一个脚本里临时拼接。优先修改 owning file。

## 代码组织约束

- 数据路径、时间周期、成本、风险、PPO 正则化：优先改 `config.py`。
- CSV 读取、时区、bar open/close、重采样、split/fold：优先改 `data_loader.py`。
- observation 特征：优先改 `features.py`。
- reward、持仓、bracket action、M1 intrabar TP/SL：优先改 `env_bracket.py`。
- baseline 与 pipeline smoke test：优先改 `baselines.py` / `run_pipeline.py`。
- PPO 训练、checkpoint selection、consistency gate：优先改 `train_ppo.py`。
- 指标与报告：优先改 `evaluate.py`。
- 图表和结果查看：优先改 `visualize.py` / `view_results.py`。
- sealed holdout：只改 `final_holdout_eval.py`，并保持一次性揭盲语义。

新增逻辑前先定向搜索现有 owner；不要创建平行实现。

## 文档渐进式披露规则

文档遵循 Progressive Disclosure，Agent 逐层深入，禁止全量读取：

```text
Level 0: AGENTS.md                     -> 项目 agent 规则和读取入口
Level 1: docs/OVERVIEW.md              -> 项目地图、模块和下一步入口
Level 2F: docs/feature/INDEX.md        -> 功能/研究模块索引
Level 2R: docs/reference/INDEX.md      -> 架构、接口、运行验证等稳定参考
Level 2A: docs/archive/INDEX.md        -> 历史材料，默认不读
Level 3: docs/feature/<module>/README.md / requirements.md
Level 4: 具体设计、RCA、数据流，仅任务相关时读取
```

读取规则：`AGENTS.md -> docs/OVERVIEW.md -> feature/reference INDEX -> 只读 1-3 个相关 leaf 文档`。`docs/USAGE_ZH.md` 是中文长说明，可作为项目背景，但不要替代当前代码和运行产物。

## 文档写入规则

- `docs/OVERVIEW.md` 是项目地图，不放长篇训练细节。
- `docs/feature/<module>/requirements.md` 写 expected behavior、研究验收口径、非目标。
- `docs/feature/<module>/README.md` 写 current implementation、入口脚本、产物路由。
- `docs/reference/*.md` 写长期稳定事实：架构、接口/产物契约、运行验证方式。
- `docs/archive/` 只放历史材料；活动说明不要放入 archive。
- 新增 leaf 文档顶部必须有 `> 上级：...` 反向链接。
- 修改运行方式、产物路径、接口契约或训练流程后，同步更新 owning docs。

## Repo-local Skills

- `.agent/skills/rl-trading-training`：训练、诊断、回测、可视化、避坑和 RL trading 研究操作模式。用户询问本项目训练/评估/产物/图表/部署门控时使用。

Skill 细节必须放在 skill 自身的 `references/` 或 `scripts/` 中；入口 `SKILL.md` 只做地图。

## 强制执行流程门（Mandatory Execution Gate）

本项目采用轻量 harness gate，不使用 `.cursor` 规则，也不创建 taskBoard。非 trivial 训练研究、回测结论或代码修改前必须按顺序检查：

1. **Scope check**：明确任务是训练计划、运行诊断、回测审查、图表可视化、踩坑排查还是代码改动。
2. **Context route**：从 `docs/OVERVIEW.md` 进入相关 feature/reference 文档；必要时读取 `.agent/skills/rl-trading-training/references/*`。
3. **Evidence check**：先检查 `config.py`、相关源码、`outputs/`、`models/`、报告 CSV、trade log、equity curve、`NO_DEPLOY.txt`。
4. **Stage gate**：不要跳过 `setup -> pipeline -> baseline -> PPO walk-forward -> consistency gate -> frozen holdout`。
5. **Docs impact**：如果修改了运行方式、产物契约、训练流程或重要研究口径，同步更新 docs。

## 防目标漂移（Anti-Drift）

- 每个非 trivial 任务开始时，用一句话写明目标和验收口径。
- 长任务中持续对齐当前阶段：setup / pipeline / baseline / PPO walk-forward / holdout。
- 不能因为局部图表或单个指标漂亮而偏离“跨时期 OOS 一致性”这个核心目标。
- 如果发现 sealed holdout 被用作迭代依据，立即停止并提醒风险。

## Git Worktree 隔离开发

- 大规模实验性改动、重构或替代训练流程，优先使用 git worktree 隔离。
- 单文件文档更新、小配置说明或 skill/reference 调整可直接在当前工作区操作。
- 不要回滚用户已有改动，除非用户明确要求。

## 测试规则

- 修改训练/评估逻辑后，至少运行相关轻量检查或说明未运行原因。
- 优先从 `python run_pipeline.py` 验证数据、特征、baseline 和 validation 图表。
- PPO 训练较重，不应为了简单文档变更运行。
- 修改 `.agent/skills/rl-trading-training/scripts/rl_trading_doctor.py` 后，用 Python AST 语法检查验证。

## 历史教训

1. Skill 和 harness 初始化使用通用 `.agent` 目录，不使用 `.cursor` 项目目录。
2. taskBoard / tasks WIP 机制不适用于当前初始化；本项目使用轻量 stage gates 和 docs 索引。
3. Sealed holdout 不能反复查看，否则会退化为新的 validation。
4. XAUUSD 短线结果对成本假设高度敏感，spread/slippage 不可信时不得下部署结论。
