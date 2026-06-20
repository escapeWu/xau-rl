# 图表可视化参考

本参考用于回答“如何看图”“如何生成交易图表”“怎样可视化回测结果”等问题。

## 默认图表入口

### Pipeline 自动图表

运行：

```bash
python run_pipeline.py
```

常见输出：

```text
outputs/01_val_candles_indicators.html
outputs/02_pretest_sessions_by_hour.html
outputs/03_pretest_feature_correlation.html
outputs/04_val_trades_on_chart.html
outputs/05_val_equity_drawdown.html
```

这些图主要用于 validation 期间检查数据、特征、baseline 和交易行为，不是最终 holdout 图。

### 结果查看器

使用 `view_results.py` 查看任意时间片，无需重跑训练：

```bash
python view_results.py
python view_results.py --bars 1000
python view_results.py --start 2024-01-01 --end 2024-06-01
python view_results.py --split val
python view_results.py --no-browser
```

默认读取：

```text
outputs/selected_val_trade_log.csv
outputs/selected_val_equity_curve.csv
```

如果要查看 holdout，必须显式传入 holdout 交易和权益文件，并确保这是模型冻结后的最终检查。

## 图表类型与用途

### Candles + indicators

函数：`visualize.plot_candles_with_indicators`

用于检查：

- K 线是否按预期重采样。
- EMA、RSI、ATR 是否合理。
- 时间轴是否存在明显错位或缺口。

### Session by hour

函数：`visualize.plot_sessions_by_hour`

用于检查：

- 不同 broker/server hour 的波动和成交量分布。
- session flags 是否与数据时区大致吻合。
- 是否存在异常的日内流动性模式。

### Feature correlation

函数：`visualize.plot_feature_correlation`

用于检查：

- observation 特征是否高度共线。
- 新增特征是否只是已有特征的重复表达。
- 是否需要删除冗余特征以降低过拟合风险。

### Trades on chart

函数：`visualize.plot_trades_on_chart`

用于检查：

- 交易入场、出场是否落在正确时间。
- long/short 是否集中在某一类行情。
- TP/SL bracket 是否合理。
- 是否存在看起来像未来函数的完美入场。

注意：项目在同一根 M1 candle 同时触及 TP 和 SL 时按 SL first 处理，这是保守假设。

### Equity and drawdown

函数：`visualize.plot_equity_and_drawdown`

用于检查：

- 收益是否平滑来自多笔交易，还是由少数跳变贡献。
- 回撤是否可接受。
- OOS 曲线是否持续退化。

## 推荐看图顺序

1. `01_val_candles_indicators.html`：确认数据和指标。
2. `03_pretest_feature_correlation.html`：确认特征不过度重复。
3. `04_val_trades_on_chart.html`：确认交易逻辑没有错位。
4. `05_val_equity_drawdown.html`：确认收益路径。
5. `models/sliding_oos_equity.csv`：结合 Python/Plotly 画连续 OOS 曲线。
6. Holdout 图：只在最终揭盲后查看。

## 可视化红旗

- 交易点系统性出现在大波动之前：检查时间戳与特征泄漏。
- equity 长期横盘，少数几笔贡献全部收益：统计不稳定。
- drawdown 越来越深，收益只在早期出现：策略可能失效。
- long 或 short 标记极度单边：检查是否只是吃到特定市场 regime。
- 图表时间与 CSV 时间相差一个 bar：检查 `timestamp_is_bar_open`。

## 生成自定义图的默认做法

优先复用 `visualize.py` 中的函数，不要重新造一套指标计算逻辑。需要自定义切片时，优先用 `view_results.py` 的 CLI 或 `view_slice()` API。
