# Harness 风格操作模式

本参考吸收 harness skills 中适合本项目的部分：渐进式披露、模式选择、证据优先、阶段门禁、结构化输出。明确不引入 taskboard、tasks 目录或 WIP task-board 机制。

## 借鉴的模式

- **Progressive disclosure**：入口文件只做地图，细节按任务读取 1-3 个 reference。
- **Mode first**：先判断当前问题属于训练计划、运行诊断、回测审查、图表可视化、踩坑排查还是代码改动规划。
- **Evidence before verdict**：先看配置、产物、指标、图表和 `NO_DEPLOY`，再给结论。
- **Stage gates**：每个阶段有明确准入条件，不跳过前置阶段。
- **Structured output**：回答要包含当前阶段、证据、结论、下一步。

## 明确不采用

- 不创建 taskBoard。
- 不维护 `.agent/.../tasks/` WIP 执行板。
- 不把研究过程包装成工程任务看板。
- 不用 holdout 反复驱动调参。

## 证据层级

借鉴 harness 的“docs as map, code/artifacts as truth”原则：

1. **配置与代码**：`config.py`, `data_loader.py`, `features.py`, `env_bracket.py`, `train_ppo.py` 是事实来源。
2. **运行产物**：`outputs/`, `models/`, trade log, equity curve, report CSV 是结果证据。
3. **项目文档**：`docs/USAGE_ZH.md` 和本 skill references 是导航和口径说明；若与代码/产物冲突，以当前代码/产物为准。
4. **结论表述**：必须说明证据来自哪个 split/fold/artifact，不用笼统结论替代证据。

## Targeted search recipes

需要定位 owner 或验证口径时，优先做定向搜索，不全量读取仓库：

```bash
# 配置、切分、成本、gate
rg -n "train_frac|test_frac|spread_price|NO_DEPLOY|gate_|sliding_" config.py train_ppo.py

# 数据读取、时间戳、重采样
rg -n "timestamp_is_bar_open|source_tz|resample|split_train_val_test|make_sliding" data_loader.py train_ppo.py config.py

# reward、bracket、执行模拟
rg -n "reward|holding_penalty|sl_atr|tp_r|SL first|MultiDiscrete" env_bracket.py config.py

# 图表和结果查看
rg -n "plot_|write_html|selected_val|holdout|view_slice" visualize.py view_results.py run_pipeline.py final_holdout_eval.py
```

当搜索结果有多个候选 owner，优先修改“如果行为坏掉，其附近测试/产物最可能失败”的文件。

## 边界规则

- Doctor 脚本只做诊断，不修改训练逻辑。
- 可视化只解释和展示，不改变评估指标。
- `final_holdout_eval.py` 只用于冻结后揭盲，不作为调参循环入口。
- 新增特征优先放 `features.py`，不要在训练脚本里临时拼接 observation。
- reward/执行假设优先放 `env_bracket.py` 或 `config.py`，不要分散到 evaluation 脚本。
- 长期说明优先更新现有 reference 或 `docs/USAGE_ZH.md`，不要制造平行文档体系。

## 模式 A：训练计划

用于用户问“怎么训练”“推荐训练顺序”“参数怎么调”。

读取：

1. `references/training-workflow.md`
2. 必要时 `docs/USAGE_ZH.md`
3. 涉及验证口径时再读 `references/backtesting-evaluation.md`

回答结构：

```text
当前阶段：setup / pipeline / baseline / PPO walk-forward / frozen holdout
推荐命令：...
准入条件：...
重点产物：...
不要做：...
```

## 模式 B：运行诊断

用于用户问“这个 run 怎么看”“为什么没有结果”“能不能部署”。

默认先运行或建议运行：

```bash
python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py
```

证据优先级：

1. `config.py` 当前配置。
2. validation 产物：`outputs/*`。
3. walk-forward 产物：`models/sliding_*`, `models/NO_DEPLOY.txt`。
4. sealed holdout 产物：只在模型冻结后解释，不用于迭代建议。

## 模式 C：回测审查

用于用户问“回测是否可信”“指标怎么看”“OOS 是否稳定”。

读取：`references/backtesting-evaluation.md`。

必须区分：

- validation-only baseline；
- sliding walk-forward OOS；
- sealed holdout。

结论模板：

```text
该结论来自：validation / sliding walk-forward OOS / sealed holdout
关键指标：return、max DD、PF、Sharpe-like、n_trades
一致性：通过/未通过/证据不足
部署状态：deployable / research-only / cannot tell
下一步：...
```

## 模式 D：图表可视化

用于用户问“怎么画图”“看哪些图”“图表说明什么”。

读取：`references/chart-visualization.md`。

默认顺序：

```text
candles + indicators
feature correlation
trades on chart
sliding OOS equity
holdout charts only after freeze
```

## 模式 E：踩坑/Debug

用于训练不稳定、验证崩掉、收益异常漂亮、交易极少、图表错位等问题。

读取：`references/common-pitfalls.md`。

优先排查：

1. 数据路径、列名、时区。
2. `timestamp_is_bar_open` 是否与数据源一致。
3. 成本设置是否现实。
4. 是否跳过了 `run_pipeline.py`。
5. 是否反复看 holdout。
6. 是否存在 `NO_DEPLOY.txt`。

## 模式 F：代码改动规划

用于用户要改特征、reward、bracket、PPO 参数、可视化或评估逻辑。

采用 harness 的“先找 owner，再改最近 owner”原则：

- 数据读取/时区/重采样：`data_loader.py`, `config.py`
- 特征：`features.py`
- 环境/reward/执行模拟：`env_bracket.py`
- baseline：`baselines.py`, `run_pipeline.py`
- PPO 训练/selection/gate：`train_ppo.py`, `config.py`
- 指标：`evaluate.py`
- 图表：`visualize.py`, `view_results.py`
- sealed holdout：`final_holdout_eval.py`

改动原则：

- 先 grep/读取现有 owner，不新增平行逻辑。
- 一次实验只改一个主要变量。
- 不为诊断脚本修改训练逻辑。
- 改配置后在回答里记录变更点。
- 涉及 docs 变化时优先更新已有文档，不新建重复文档。

## Stage gates

```text
G0 setup
  数据文件存在，config 可加载，成本/时区/timeframe 明确
        ▼
G1 pipeline
  run_pipeline.py 通过，validation 图表和 baseline 产物可读
        ▼
G2 baseline sanity
  baseline 行为可解释，交易日志/权益曲线无明显错位
        ▼
G3 PPO walk-forward
  train_ppo.py 完成，多 fold OOS 有足够交易样本
        ▼
G4 consistency gate
  fold 一致性、PF、Sharpe-like、NO_DEPLOY 状态明确
        ▼
G5 frozen holdout
  模型和配置冻结后，仅揭盲一次 sealed holdout
```

不要建议用户从 G0 直接跳到 G5。
