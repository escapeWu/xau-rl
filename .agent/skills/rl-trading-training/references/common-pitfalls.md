# 常见坑与排查清单

本参考用于回答“哪里容易踩坑”“为什么回测很好实盘不行”“训练为什么不稳定”等问题。

## 数据与时间戳

### Candle open / close 错位

MT4/MT5 M1 导出通常用 candle open time。项目内部把索引转为 candle close time，使决策时刻只看到已经完成的 K 线。

检查 `config.py`：

```python
timestamp_is_bar_open = True
```

如果数据源已经是 close time，却仍设为 `True`，会多平移一次，造成决策和成交错位。

### 时区假设错误

默认：

```python
source_tz = "Europe/Helsinki"
```

这适合很多标注 EET/EEST 的 broker 数据。如果数据源不是 EET/EEST，要先改配置，不要在后续训练逻辑里硬修。

### 随机切分时间序列

交易数据不能随机 train/test split。必须按时间顺序切分，并用 walk-forward 检查跨时期稳定性。

## 特征泄漏与非平稳

### 使用绝对价格

XAUUSD 跨年份价格尺度变化明显。直接输入 Open/High/Low/Close 容易让模型学习非平稳关系。

优先使用：

- ATR-normalized distance。
- 比例类特征。
- session/time sin-cos。
- candle shape ratio。

### 特征看到了未来

每个 timestamp 的特征只能使用当时及之前已经完成的数据。新增特征后要检查 rolling、shift、resample 的方向。

### 高度共线

高度重复的特征会放大过拟合风险。新增特征后查看 correlation heatmap。

## 训练与验证

### 直接跑 PPO

不要跳过 `run_pipeline.py`。如果 baseline、特征、图表都没跑通，PPO 的问题很难定位。

### 只看最后 checkpoint

PPO 后期可能过拟合。优先使用项目 checkpoint selection 选出的 best model，不要默认最后一步最好。

### 反复看 holdout

`final_holdout_eval.py` 只能在模型冻结后运行。如果根据 holdout 继续调参，holdout 就变成新的 validation。

### 忽略 VecNormalize

SB3 模型需要匹配保存时的 normalization 状态。检查 best model 是否同时有：

```text
best_model.zip
best_model_vecnorm.pkl
```

## 成本与执行

### 交易成本太乐观

黄金短线对 spread、slippage、commission 极敏感。检查：

```python
spread_price
slippage_price
commission_per_trade
```

成本假设不可信时，任何收益曲线都不能当真。

### 忽略 M1 intrabar 顺序

只看 H1 candle 无法判断先 TP 还是先 SL。本项目保留 M1 执行层，并在同一根 M1 candle 同时触及时按 SL first 处理。

### bracket 空间过大或过小

过小会限制策略，过大让探索变难。默认先用少量 bucket，再根据 OOS 行为扩展。

## 结果解释

### 单折漂亮不代表有效

多折 OOS 一致性比单次收益重要。只有一个 fold 暴赚时，先怀疑运气或行情特例。

### 交易太少

`n_trades` 太少时，profit factor、win rate、total return 都不稳定。

### NO_DEPLOY 被忽略

如果存在：

```text
models/NO_DEPLOY.txt
```

必须把结果表述为 research-only，不要称为可部署策略。

## 快速排查顺序

1. 跑 `python .agent/skills/rl-trading-training/scripts/rl_trading_doctor.py`。
2. 检查 `config.py` 的数据路径、时区、timestamp、成本。
3. 跑 `python run_pipeline.py`。
4. 看 validation 图表是否合理。
5. 跑 `python train_ppo.py`。
6. 看每折 OOS，不只看平均值。
7. gate 通过后再考虑 sealed holdout。
