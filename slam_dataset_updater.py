#!/usr/bin/env python3
"""Discover and curate 3-D LiDAR SLAM datasets referenced by GitHub projects.

The updater is intentionally conservative: a record is published only when both
3-D LiDAR evidence and trajectory ground-truth evidence are present.  An AI
model can improve the human-readable fields, but it is never allowed to bypass
those checks.

The Anthropic-compatible Messages API settings match ``paper_update``:
``ANTHROPIC_AUTH_TOKEN``, ``ANTHROPIC_BASE_URL`` and ``ANTHROPIC_MODEL``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urljoin, urlparse

import requests
import yaml


LOG = logging.getLogger("slam-dataset-updater")
TODAY = dt.date.today().isoformat()

# These patterns are deliberately broad for discovery, then combined with the
# strict evidence check below.  They cover common names used by robotics data.
LIDAR_PATTERNS = (
    r"\b3d\s*(?:li?dar|laser)\b",
    r"\b(?:velodyne|ouster|livox|hesai|robosense)\b",
    r"\b(?:hdl[- ]?32|hdl[- ]?64|os[0-9][- ]?(?:32|64)|mid[- ]?70)\b",
    r"\b3d\s+point\s*cloud(?:s)?\b",
)
GROUND_TRUTH_PATTERNS = (
    r"ground[- ]truth\s+(?:pose|poses|trajectory|trajectories|odometry)",
    r"(?:pose|poses|trajectory|trajectories|odometry)\s+(?:ground[- ]truth|gt|truth)",
    r"reference\s+(?:pose|poses|trajectory|trajectories|odometry)",
    r"\b(?:rtk|gnss|gps/imu|gps\s*[-+]\s*imu|applanix|leica|motion capture|mocap)\b.{0,100}\bground[- ]truth\b",
    r"\bground[- ]truth\b.{0,100}\b(?:rtk|gnss|gps/imu|gps\s*[-+]\s*imu|applanix|leica|motion capture|mocap)\b",
)
URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")

SCENARIOS = (
    "汽车/自动驾驶",
    "室内移动机器人",
    "机器狗/四足机器人",
    "户外/越野机器人",
    "无人机/空中机器人",
    "混合场景",
)


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def clean_url(url: str) -> str:
    """Remove punctuation commonly captured after a Markdown URL."""
    return url.rstrip(".,;:!?\"'`>")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "dataset"


def unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def text_of(record: Mapping[str, Any]) -> str:
    gt = record.get("ground_truth", {})
    gt_notes = gt.get("notes", "") if isinstance(gt, Mapping) else str(gt or "")
    parts = [
        str(record.get("name", "")),
        str(record.get("description", "")),
        str(record.get("readme_excerpt", "")),
        str(gt_notes),
    ]
    sensors = record.get("sensors", {})
    if isinstance(sensors, Mapping):
        parts.extend(str(v) for v in sensors.values())
    return " ".join(parts)


def evidence_matches(text: str, patterns: Sequence[str]) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in patterns if re.search(pattern, lowered)]


def evidence_terms(text: str, patterns: Sequence[str]) -> list[str]:
    """Return the actual phrases found, suitable for a human audit trail."""
    terms: list[str] = []
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            terms.append(match.group(0))
    return unique(terms)


def has_3d_lidar(record: Mapping[str, Any]) -> bool:
    sensors = record.get("sensors", {})
    explicit = sensors.get("lidar_3d") if isinstance(sensors, Mapping) else None
    if explicit:
        explicit_text = str(explicit).strip()
        if explicit_text.lower() not in {"no", "none", "false", "unknown"} and evidence_matches(explicit_text, LIDAR_PATTERNS):
            return True
    return bool(evidence_matches(text_of(record), LIDAR_PATTERNS))


def has_ground_truth(record: Mapping[str, Any]) -> bool:
    gt = record.get("ground_truth", {})
    if isinstance(gt, Mapping) and as_bool(gt.get("available"), False):
        return True
    return bool(evidence_matches(text_of(record), GROUND_TRUTH_PATTERNS))


def infer_scenario(text: str) -> str:
    lowered = text.lower()
    if re.search(r"quadruped|four[- ]leg|robot dog|anymal|spot robot", lowered):
        return "机器狗/四足机器人"
    if re.search(r"uav|drone|aerial|无人机|multirotor", lowered):
        return "无人机/空中机器人"
    if re.search(r"car|vehicle|automotive|autonomous driving|road|urban", lowered):
        return "汽车/自动驾驶"
    if re.search(r"indoor|warehouse|office|corridor|室内", lowered):
        return "室内移动机器人"
    if re.search(r"off[- ]road|outdoor|terrain|campus|trail|越野", lowered):
        return "户外/越野机器人"
    return "混合场景"


def infer_platform(text: str) -> str:
    lowered = text.lower()
    if re.search(r"quadruped|robot dog|anymal|spot robot", lowered):
        return "机器狗/四足机器人"
    if re.search(r"car|vehicle|automotive|driving", lowered):
        return "汽车"
    if re.search(r"uav|drone|aerial", lowered):
        return "无人机"
    if re.search(r"handheld|backpack", lowered):
        return "手持/背负式平台"
    return "移动机器人"


def extract_links(readme: str, base_url: str = "") -> list[str]:
    links = [clean_url(x) for x in MARKDOWN_LINK_RE.findall(readme)]
    links.extend(clean_url(x) for x in URL_RE.findall(readme))
    result = []
    for link in unique(links):
        if link.startswith("/") and base_url:
            link = urljoin(base_url, link)
        parsed = urlparse(link)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            result.append(link)
    return unique(result)


def choose_dataset_links(links: Sequence[str], project_url: str) -> list[str]:
    """Prefer official dataset/download/documentation URLs over badges."""
    project_host = urlparse(project_url).netloc.lower()
    skip = ("travis-ci", "badge", "shields.io", "github.com/actions")
    scored: list[tuple[int, str]] = []
    for link in links:
        lowered = link.lower()
        if any(token in lowered for token in skip):
            continue
        score = 0
        if any(token in lowered for token in ("dataset", "data", "download", "benchmark", "ground", "trajectory")):
            score += 3
        if "github.com" not in lowered or urlparse(link).netloc.lower() != project_host:
            score += 1
        scored.append((score, link))
    return [link for _, link in sorted(scored, key=lambda item: (-item[0], item[1]))]


@dataclass
class GitHubClient:
    token: str = ""
    timeout: int = 30
    max_retries: int = 3

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "User-Agent": "slam-dataset-updater",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def get(self, url: str, **kwargs: Any) -> requests.Response | None:
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                if response.status_code in {429, 500, 502, 503, 504} and attempt + 1 < self.max_retries:
                    time.sleep(2**attempt)
                    continue
                return response
            except requests.RequestException as exc:
                if attempt + 1 == self.max_retries:
                    LOG.warning("GitHub 请求失败 %s: %s", url, exc)
                else:
                    time.sleep(2**attempt)
        return None

    def search_repositories(self, query: str, limit: int) -> list[dict[str, Any]]:
        response = self.get("https://api.github.com/search/repositories", params={
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max(limit, 1), 100),
        })
        if not response or response.status_code != 200:
            if response:
                LOG.warning("GitHub 搜索失败 (%s): %s", response.status_code, response.text[:200])
            return []
        items = response.json().get("items", [])
        return [item for item in items if isinstance(item, dict)][:limit]

    def readme(self, full_name: str) -> str:
        response = self.get(f"https://api.github.com/repos/{full_name}/readme", headers={
            "Accept": "application/vnd.github.raw+json",
        })
        if response and response.status_code == 200:
            return response.text
        LOG.debug("没有读取到 README: %s", full_name)
        return ""


class AIEnricher:
    """Small, optional AI layer compatible with paper_update's API setup."""

    def __init__(self, enabled: bool = True, timeout: int = 120, retries: int = 3) -> None:
        self.enabled = enabled and bool(env("ANTHROPIC_AUTH_TOKEN"))
        self.api_key = env("ANTHROPIC_AUTH_TOKEN")
        self.base_url = env("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        self.model = env("ANTHROPIC_MODEL", "minimax-m3")
        self.url = f"{self.base_url}/v1/messages"
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def enrich(self, record: Mapping[str, Any]) -> dict[str, Any]:
        fallback = deterministic_enrichment(record)
        if not self.enabled:
            return fallback
        prompt = (
            "你是机器人 SLAM 数据集整理助手。仅根据给出的证据返回一个 JSON 对象，"
            "不要添加 Markdown 或额外文字。不得声称证据中没有的传感器或真值。\n"
            "JSON 字段必须为: scenario, platform, description_zh, sensor_notes, "
            "ground_truth_notes, confidence。scenario 从 [汽车/自动驾驶, 室内移动机器人, "
            "机器狗/四足机器人, 户外/越野机器人, 无人机/空中机器人, 混合场景] 中选择；"
            "confidence 为 0 到 1 的数字。\n证据:\n"
            + json.dumps(record, ensure_ascii=False, indent=2)[:12000]
        )
        body = {"model": self.model, "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        for attempt in range(self.retries):
            try:
                response = self.session.post(self.url, headers=headers, json=body, timeout=self.timeout)
                if response.status_code != 200:
                    LOG.warning("AI API 响应错误 (%s): %s", response.status_code, response.text[:200])
                    continue
                data = response.json()
                content = data.get("content", [])
                raw = next((item.get("text", "") for item in content if item.get("type") == "text"), "")
                parsed = parse_json_object(raw)
                if parsed:
                    return merge_enrichment(fallback, parsed)
            except (requests.RequestException, ValueError, TypeError) as exc:
                LOG.warning("AI API 调用失败 (尝试 %s/%s): %s", attempt + 1, self.retries, exc)
            if attempt + 1 < self.retries:
                time.sleep(2**attempt)
        return fallback


def parse_json_object(value: str) -> dict[str, Any]:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


def deterministic_enrichment(record: Mapping[str, Any]) -> dict[str, Any]:
    text = text_of(record)
    sensors = record.get("sensors", {})
    sensor_notes = []
    if isinstance(sensors, Mapping):
        for label, value in sensors.items():
            if value and label != "lidar_3d":
                sensor_notes.append(f"{label}: {value}")
    gt = record.get("ground_truth", {})
    gt_notes = gt.get("notes", "") if isinstance(gt, Mapping) else ""
    return {
        "scenario": record.get("scenario") if record.get("scenario") in SCENARIOS else infer_scenario(text),
        "platform": record.get("platform") or infer_platform(text),
        "description_zh": record.get("description_zh") or f"面向{infer_platform(text)}的 3D 激光 SLAM 数据集，包含可用于轨迹评估的真值。",
        "sensor_notes": "；".join(sensor_notes),
        "ground_truth_notes": gt_notes,
        "confidence": 0.65,
    }


def merge_enrichment(fallback: Mapping[str, Any], parsed: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(fallback)
    for key in ("scenario", "platform", "description_zh", "sensor_notes", "ground_truth_notes"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    confidence = parsed.get("confidence")
    try:
        result["confidence"] = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        pass
    if result.get("scenario") not in SCENARIOS:
        result["scenario"] = fallback["scenario"]
    return result


def normalize_record(raw: Mapping[str, Any], source: str = "curated") -> dict[str, Any]:
    record = dict(raw)
    record["name"] = str(record.get("name") or record.get("id") or "未命名数据集").strip()
    record["id"] = str(record.get("id") or slugify(record["name"]))
    record["source"] = source
    for key in ("project", "dataset", "sensors", "ground_truth"):
        value = record.get(key)
        record[key] = dict(value) if isinstance(value, Mapping) else {}
    if record["project"].get("url") and not record["project"].get("docs_url"):
        record["project"]["docs_url"] = record["project"]["url"]
    links = record["dataset"].get("links", [])
    if isinstance(links, str):
        links = [links]
    record["dataset"]["links"] = unique(str(x) for x in links)
    raw_evidence = record.get("evidence") or []
    if isinstance(raw_evidence, str):
        raw_evidence = [raw_evidence]
    record["evidence"] = unique(str(x) for x in raw_evidence)
    record["last_verified"] = str(record.get("last_verified") or TODAY)
    record["readme_excerpt"] = str(record.get("readme_excerpt") or "")[:4000]
    return record


def validate_record(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    project = record.get("project", {})
    dataset = record.get("dataset", {})
    if not isinstance(project, Mapping) or not project.get("url"):
        errors.append("缺少开源工程链接")
    if not isinstance(dataset, Mapping) or not dataset.get("url"):
        errors.append("缺少数据集链接")
    if not has_3d_lidar(record):
        errors.append("没有确认 3D 激光雷达")
    if not has_ground_truth(record):
        errors.append("没有确认轨迹真值")
    return not errors, errors


def discover_from_github(client: GitHubClient, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    queries = config.get("github_search_queries", [])
    limit = int(config.get("max_repositories_per_query", 10))
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries:
        LOG.info("搜索 GitHub: %s", query)
        for item in client.search_repositories(str(query), limit):
            full_name = str(item.get("full_name", ""))
            if not full_name or full_name in seen:
                continue
            seen.add(full_name)
            project_url = str(item.get("html_url") or f"https://github.com/{full_name}")
            readme = client.readme(full_name)
            combined = " ".join(str(item.get(key, "")) for key in ("name", "description")) + " " + readme
            lidar_hits = evidence_terms(combined, LIDAR_PATTERNS)
            gt_hits = evidence_terms(combined, GROUND_TRUTH_PATTERNS)
            if not lidar_hits or not gt_hits:
                LOG.debug("跳过证据不足的仓库: %s", full_name)
                continue
            links = extract_links(readme, project_url)
            dataset_links = choose_dataset_links(links, project_url)
            if not dataset_links:
                LOG.debug("跳过没有数据集链接的仓库: %s", full_name)
                continue
            record = normalize_record({
                "id": slugify(f"{full_name}-{item.get('name', '')}"),
                "name": item.get("name") or full_name,
                "platform": infer_platform(combined),
                "project": {
                    "name": full_name,
                    "url": project_url,
                    "docs_url": project_url,
                    "stars": item.get("stargazers_count", 0),
                },
                "dataset": {"name": "README 中引用的数据集", "url": dataset_links[0], "links": dataset_links[:8]},
                "sensors": {"lidar_3d": "GitHub 项目描述/README 证据: " + ", ".join(lidar_hits)},
                "ground_truth": {
                    "available": True,
                    "type": "README 证据待人工核验",
                    "notes": "GitHub 项目描述/README 证据: " + ", ".join(gt_hits),
                },
                "evidence": [f"GitHub README: {project_url}"] + lidar_hits + gt_hits,
                "readme_excerpt": readme[:4000],
            }, source="github")
            results.append(record)
    return results


def load_catalog(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        LOG.warning("目录文件不存在: %s", path)
        return []
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if isinstance(content, Mapping):
            content = content.get("datasets", [])
        return [normalize_record(x, source="curated") for x in content if isinstance(x, Mapping)]
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"无法读取目录 {path}: {exc}") from exc


def merge_records(records: Iterable[Mapping[str, Any]], ai: AIEnricher) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for raw in records:
        record = normalize_record(raw, source=str(raw.get("source", "github")))
        valid, errors = validate_record(record)
        if not valid:
            LOG.info("过滤 %s: %s", record["name"], "；".join(errors))
            continue
        # Dataset URL is the most stable identity; fall back to project/name.
        key = str(record["dataset"].get("url") or record["id"]).lower().rstrip("/")
        if key in by_key:
            current = by_key[key]
            current["evidence"] = unique(current.get("evidence", []) + record.get("evidence", []))
            current["dataset"]["links"] = unique(current["dataset"].get("links", []) + record["dataset"].get("links", []))
            continue
        enriched = dict(record)
        # Human-verified text is stable across scheduled runs. AI is reserved
        # for newly discovered GitHub records where normalization adds value.
        enrichment = ai.enrich(record) if record.get("source") == "github" else deterministic_enrichment(record)
        enriched.update(enrichment)
        enriched["requirements"] = {"has_3d_lidar": True, "has_trajectory_ground_truth": True}
        by_key[key] = enriched
    return sorted(by_key.values(), key=lambda item: (str(item.get("scenario", "")), str(item.get("name", "")).lower()))


def write_json(records: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": TODAY, "count": len(records), "datasets": records}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def md_link(label: Any, url: Any) -> str:
    return f"[{html.escape(str(label or url))}]({html.escape(str(url))})" if url else "未提供"


def write_markdown(records: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get("scenario") or "混合场景"), []).append(record)
    lines = [
        "# 机器人 3D 激光 SLAM 数据集目录",
        "",
        f"> 自动生成于 {TODAY}。仅收录同时确认包含 3D 激光雷达和轨迹真值的数据集；README 发现项仍需人工复核。",
        "",
        f"共 **{len(records)}** 个数据集。字段详情见 [JSON 数据](slam-datasets.json)。",
        "",
        "## 筛选规则",
        "",
        "- 必须能从官方文档、项目 README 或数据集页面确认 3D LiDAR/3D 激光型号或点云输入。",
        "- 必须提供可用于轨迹评估的 ground truth/reference trajectory（例如 INS/RTK/GNSS、Leica、MoCap）。",
        "- IMU、相机、轮速编码器等为可选传感器，缺失时明确标注。",
        "",
    ]
    for scenario in SCENARIOS:
        entries = grouped.get(scenario, [])
        if not entries:
            continue
        lines += [f"## {scenario}", "", "| 数据集 | 开源工程 | 传感器配置 | 轨迹真值 | 文档/数据链接 |", "| --- | --- | --- | --- | --- |"]
        for record in entries:
            project = record.get("project", {})
            dataset = record.get("dataset", {})
            sensors = record.get("sensors", {})
            gt = record.get("ground_truth", {})
            sensor_parts = [f"3D LiDAR: {sensors.get('lidar_3d', '已确认')}" ]
            for key, label in (("imu", "IMU"), ("camera", "视觉"), ("wheel_encoder", "编码器"), ("gnss", "GNSS/RTK"), ("uwb", "UWB")):
                if sensors.get(key):
                    sensor_parts.append(f"{label}: {sensors[key]}")
            docs = project.get("docs_url") or project.get("url")
            dataset_links = dataset.get("links") or []
            link_text = md_link("数据集", dataset.get("url"))
            if docs and docs != dataset.get("url"):
                link_text += " / " + md_link("文档", docs)
            if dataset_links:
                link_text += " / " + " / ".join(md_link(f"链接{i}", link) for i, link in enumerate(dataset_links[:3], 1))
            lines.append(
                "| {name}<br>{desc} | {project} | {sensors} | {gt} | {links} |".format(
                    name=html.escape(str(record.get("name", ""))),
                    desc=html.escape(str(record.get("description_zh", ""))),
                    project=md_link(project.get("name", "工程"), project.get("url")),
                    sensors="<br>".join(html.escape(part) for part in sensor_parts),
                    gt=html.escape(str(gt.get("type") or gt.get("notes") or "已确认")),
                    links=link_text,
                )
            )
        lines.append("")
    if not records:
        lines += ["目前没有通过硬过滤的数据集。", ""]
    lines += ["## 维护", "", "由 `slam_dataset_updater.py` 通过 GitHub Actions 定时更新。修改 `config.yaml` 中的搜索词或 workflow 的 cron 即可调整范围和时间。", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def load_config(path: Path) -> dict[str, Any]:
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"无法读取配置 {path}: {exc}") from exc
    if not isinstance(config, dict):
        raise RuntimeError("配置根节点必须是 YAML 对象")
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="整理 GitHub 上含 3D LiDAR 和轨迹真值的机器人 SLAM 数据集")
    parser.add_argument("--config", "--config_path", dest="config", default="config.yaml", help="YAML 配置文件")
    parser.add_argument("--catalog", default="data/curated_datasets.yaml", help="人工核验的种子目录")
    parser.add_argument("--output-json", help="覆盖 JSON 输出路径")
    parser.add_argument("--output-markdown", help="覆盖 Markdown 输出路径")
    parser.add_argument("--no-github", action="store_true", help="只处理种子目录")
    parser.add_argument("--no-ai", action="store_true", help="禁用 AI 富化")
    parser.add_argument("--dry-run", action="store_true", help="只在终端输出统计，不写文件")
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="[%(asctime)s %(levelname)s] %(message)s")
    config = load_config(Path(args.config))
    records = load_catalog(Path(args.catalog))
    if not args.no_github and as_bool(config.get("github", {}).get("enabled"), True):
        github = GitHubClient(token=env("GITHUB_TOKEN"), timeout=int(config.get("github", {}).get("timeout", 30)))
        records.extend(discover_from_github(github, config.get("github", {})))
    ai_config = config.get("ai", {})
    ai_enabled = as_bool(ai_config.get("enabled"), True) and not args.no_ai
    curated = merge_records(records, AIEnricher(enabled=ai_enabled, timeout=int(ai_config.get("timeout", 120))))
    output_json = Path(args.output_json or config.get("output", {}).get("json", "docs/slam-datasets.json"))
    output_markdown = Path(args.output_markdown or config.get("output", {}).get("markdown", "docs/slam-datasets.md"))
    if args.dry_run:
        print(json.dumps({"count": len(curated), "scenarios": sorted({r.get("scenario") for r in curated})}, ensure_ascii=False))
        return 0
    write_json(curated, output_json)
    write_markdown(curated, output_markdown)
    LOG.info("已写入 %s 个数据集: %s, %s", len(curated), output_json, output_markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
