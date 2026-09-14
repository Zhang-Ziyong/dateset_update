# 机器人 3D 激光 SLAM 数据集整理器

这个仓库用 GitHub Actions 定时搜索 GitHub 上的机器人 SLAM/LIO 工程，抽取其 README 中引用的数据集，并与人工核验目录合并，生成按使用场景分类的目录：

- [数据集目录（Markdown）](docs/slam-datasets.md)
- [数据集目录（JSON）](docs/slam-datasets.json)

每条记录包含数据集链接、对应开源工程和文档链接、平台/使用场景、传感器配置、轨迹真值类型和证据链接。硬过滤要求是：**必须确认 3D LiDAR，且必须有可用于轨迹评估的 ground-truth/reference trajectory**。IMU、相机、轮速编码器和 GNSS 等传感器按实际资料填写，没有证据就不臆测。

## 本地运行

```bash
python3 -m pip install -r requirements.txt
python3 slam_dataset_updater.py --config config.yaml --catalog data/curated_datasets.yaml
```

无网络或没有 GitHub Token 时可以只处理人工核验目录：

```bash
python3 slam_dataset_updater.py --no-github --no-ai
```

先检查数量而不写文件：

```bash
python3 slam_dataset_updater.py --dry-run --no-github --no-ai
```

## GitHub Actions 与 AI

`.github/workflows/update-slam-datasets.yml` 默认每周一 UTC 01:30 运行（北京时间 09:30），也支持 `workflow_dispatch` 手动运行。按需要修改 workflow 中的 cron 表达式；GitHub Actions 的 cron 使用 UTC。

GitHub 搜索使用 `GITHUB_TOKEN`，未配置时仍会使用较低速率的匿名 API。AI 富化沿用 `/home/zhang/Workspace/paper_update` 的兼容 Anthropic Messages API 方式：配置仓库 secrets `ANTHROPIC_AUTH_TOKEN`，可选 `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_MODEL`。AI 只生成中文描述、场景和备注，不能绕过 3D LiDAR/轨迹真值校验；没有 Token 时自动使用确定性回退，不会导致任务失败。

## 增加人工核验条目

编辑 `data/curated_datasets.yaml`，至少提供：

1. `project.url`（开源工程）和 `dataset.url`（数据集）；
2. `sensors.lidar_3d` 的具体 3D 激光型号或可靠描述；
3. `ground_truth.available: true` 和轨迹来源/类型；
4. `project.docs_url`、`dataset.links` 与 `evidence`，便于复核。

脚本会按数据集 URL 去重，并把不满足硬条件的条目记录过滤日志。
