# Chart Visualization

> 上级：[`README.md`](README.md)

本文件整理本项目图表和可视化检查口径。更细的 agent 操作提示见 [`.agent/skills/rl-trading-training/references/chart-visualization.md`](../../../.agent/skills/rl-trading-training/references/chart-visualization.md)。

## Default Chart Entry Points

### Pipeline Charts

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

这些图主要用于 validation 期间检查数据、特征、baseline 和交易行为。

### Slice Viewer

使用 `view_results.py` 读取已保存 trade/equity CSV 生成切片图表：

```bash
python view_results.py --bars 1000
python view_results.py --start 2024-01-01 --end 2024-06-01
python view_results.py --split val --no-browser
```

默认读取 validation artifacts。查看 holdout 图时必须显式传入 holdout trade/equity 文件，并确认模型已冻结。

## Chart Types

| Chart | Function | Main purpose |
|-------|----------|--------------|
| Candles + indicators | `plot_candles_with_indicators` | 检查 OHLC、EMA、RSI、ATR 和时间轴 |
| Session by hour | `plot_sessions_by_hour` | 检查 broker/server hour 的波动和 volume 分布 |
| Feature correlation | `plot_feature_correlation` | 检查 observation 特征共线性 |
| Trades on chart | `plot_trades_on_chart` | 检查入场、出场、TP/SL bracket 和时间错位 |
| Equity + drawdown | `plot_equity_and_drawdown` | 检查收益路径、回撤和少数交易贡献问题 |

## Recommended Viewing Order

1. `01_val_candles_indicators.html`
2. `03_pretest_feature_correlation.html`
3. `04_val_trades_on_chart.html`
4. `05_val_equity_drawdown.html`
5. `models/sliding_oos_equity.csv` 的连续 OOS 曲线
6. frozen holdout 相关图表

## Visualization Red Flags

- 交易点系统性出现在大波动前：检查时间戳和特征泄漏。
- equity 长期横盘但少数跳变贡献全部收益：统计不稳定。
- drawdown 持续加深且收益只在早期出现：策略可能失效。
- long/short 极端单边：可能只适配某段市场 regime。
- 图表时间与 CSV 时间差一个 bar：检查 `timestamp_is_bar_open`。

## Boundary

可视化逻辑不应改变训练、评估或指标计算。自定义图优先复用 `visualize.py` 和 `view_results.py`，不要在图表脚本里重新实现训练/评估逻辑。
