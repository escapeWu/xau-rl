# Pitfalls and Debugging

> 上级：[`README.md`](README.md)

本文件整理本项目训练、回测和可视化中最容易踩坑的稳定排查口径。更细的 agent 操作提示见 [`.agent/skills/rl-trading-training/references/common-pitfalls.md`](../../../.agent/skills/rl-trading-training/references/common-pitfalls.md)。

## Data and Timestamp Pitfalls

### Candle open / close offset

MT4/MT5 M1 导出通常用 candle open time。项目内部以 close time 表示“这根 K 线已经完成并可被模型看到”。

重点配置：

```python
timestamp_is_bar_open = True
```

如果数据源已经是 close time，却仍设为 `True`，会多平移一次，导致决策、入场和图表全部错位。

### Timezone mismatch

默认：

```python
source_tz = "Europe/Helsinki"
```

如果 broker 数据不是 EET/EEST 口径，优先改 `config.py`，不要在训练或评估脚本里临时修时间。

### Random split

交易数据不能随机切分。必须使用时间顺序 split，并用 walk-forward 检查跨时期稳定性。

## Feature Pitfalls

- 不要直接把绝对 Open/High/Low/Close 当 observation 喂给 PPO。
- 新增 rolling/shift/resample 特征时，必须确认每个 timestamp 只使用当前及过去完成的 bar。
- 新增特征后查看 correlation heatmap，避免高度共线特征放大过拟合。

## Training Pitfalls

- 不要跳过 `python run_pipeline.py` 直接跑 PPO。
- 不要默认最后 checkpoint 最好；优先使用项目 checkpoint selection 选出的 best model。
- SB3 模型必须配套 VecNormalize：`best_model.zip` 与 `best_model_vecnorm.pkl` 应成对存在。
- 不要反复运行 `final_holdout_eval.py` 来驱动调参。

## Cost and Execution Pitfalls

黄金短线对成本极敏感。检查：

```python
spread_price
slippage_price
commission_per_trade
```

成本假设不可信时，收益曲线不能当成策略证据。

执行层保留 M1 是为了判断 TP/SL intrabar 触发顺序；同一根 M1 candle 同时触及 TP 和 SL 时，项目采用保守的 SL-first 假设。

## Result Interpretation Pitfalls

- 单个 fold 暴赚不等于有 edge。
- `n_trades` 太少时，PF、win rate 和 total return 都不稳定。
- long/short 极端单边时，要检查是否只适配某段行情。
- 如果存在 `models/NO_DEPLOY.txt`，必须把该 run 表述为 research-only。

## Debug Order

1. 运行 `python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py`。
2. 检查 `config.py` 的数据路径、时区、timestamp、成本。
3. 跑 `python run_pipeline.py`。
4. 看 validation 图表是否有时间错位或未来函数迹象。
5. 跑 `python train_ppo.py`。
6. 逐 fold 看 OOS，不只看平均值。
7. gate 通过后，且模型冻结后，才考虑 sealed holdout。
