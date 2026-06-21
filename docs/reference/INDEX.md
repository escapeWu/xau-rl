# Reference Index

> 上级：[`../OVERVIEW.md`](../OVERVIEW.md)

稳定技术事实、产物契约和运行验证入口放在这里。需要训练细节时优先从 feature README 进入；需要长期不随单次实验变化的规则时进入本目录。

## Reference Docs

| File | Purpose |
|------|---------|
| [`architecture.md`](architecture.md) | 项目层次、模块边界、数据流和 owner map |
| [`interfaces.md`](interfaces.md) | 数据输入、配置、报告、trade/equity、模型产物契约 |
| [`runbook-testing.md`](runbook-testing.md) | 安装、doctor、pipeline、训练、可视化和 holdout 验证步骤 |
| [`dashboard.md`](dashboard.md) | 本地 React/Tailwind 看板、API 和产物浏览说明 |
| [`project-memory.md`](project-memory.md) | 跨模块长期记忆、稳定研究立场和已废弃路径 |

## Reading Rule

1. 架构/owner/边界问题读 `architecture.md`。
2. CSV、配置、产物字段或模型文件口径读 `interfaces.md`。
3. 要运行命令、检查结果或验证 harness 初始化读 `runbook-testing.md`。
4. 要确认长期项目记忆、稳定禁忌或已废弃做法读 `project-memory.md`。

不要把单次实验结论写入 reference；单次结论应进入运行产物或归档说明。
