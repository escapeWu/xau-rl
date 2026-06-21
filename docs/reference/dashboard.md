# Local Dashboard

> 上级：[`INDEX.md`](INDEX.md)

本项目提供一个本地只读看板，用于浏览 `outputs/`、`models/`、`notebooks/` 和 `logs/` 下的训练结果、CSV、HTML 图表与图片。它不读取任意路径，也不暴露密钥或 broker 账户信息。

## 启动

```bash
scripts/run_dashboard.sh
```

默认地址：

```text
http://127.0.0.1:5180
```

默认监听 `0.0.0.0:5180`，因此同一局域网内也可以通过本机 LAN IP 访问，例如：

```text
http://192.168.5.33:5180
```

脚本会在首次运行时安装 `dashboard/` 依赖并构建前端，然后启动 Python 标准库 HTTP API。

开发前端时可以分两个终端运行：

```bash
python scripts/dashboard_api.py
cd dashboard && npm run dev
```

开发模式前端地址：

```text
http://127.0.0.1:5173
```

## 展示内容

看板读取这些本地产物：

```text
outputs/performance_report.csv
outputs/selected_policy.csv
outputs/walk_forward_baseline.csv
outputs/*.html
models/sliding_walk_forward_summary.csv
models/sliding_oos_equity.csv
models/run_info.json
models/NO_DEPLOY.txt
notebooks/*.png
logs/*
```

它会显示：

- 当前 selected validation 指标：return、profit factor、max drawdown、trades。
- baseline validation 对照。
- selected policy 参数。
- PPO walk-forward summary；训练未完成时显示 pending。
- HTML 图表 iframe 预览。
- 图片预览。
- CSV/JSON/text 文件预览。
- 模型 gate 状态和 `NO_DEPLOY.txt` 内容。

## API

```text
GET /api/status
GET /api/file?path=<artifact-relative-path>
GET /api/preview?path=<artifact-relative-path>
```

`path` 只能指向以下目录内的文件：

```text
outputs/
models/
notebooks/
logs/
```

允许的文件类型：

```text
.csv .json .txt .log .md .html .htm .png .jpg .jpeg .webp .gif .svg
```

## 注意事项

- `data/` 不被看板暴露，避免浏览器读取大规模原始行情数据。
- `outputs/` 和 `models/` 是运行产物，通常被 `.gitignore` 忽略。
- 看板只负责查看结果，不执行训练、不揭盲 sealed holdout。
