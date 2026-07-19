# -*- coding: utf-8 -*-
"""
每日 AI 播客脚本生成和生成任务编排。
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta

import requests

from config import (
    AI_API_URL,
    GITHUB_TOKEN,
    OUTPUT_ARCHIVE_DIR,
    PODCAST_ENABLED,
    PODCAST_EXCLUDED_SOURCE_IDS,
    PODCAST_MAX_DURATION_MINUTES,
    PODCAST_SCRIPT_MAX_RETRIES,
    PODCAST_SCRIPT_MODEL,
    PODCAST_SCRIPT_PROVIDER,
    PODCAST_SCRIPT_RETRY_SECONDS,
    PODCAST_TARGET_DATE_MODE,
)
from content_store import load_history_archive_snapshot
from podcast_store import (
    acquire_podcast_lock,
    build_failed_metadata,
    has_successful_podcast,
    load_podcast_script,
    podcast_dir,
    release_podcast_lock,
    write_podcast_metadata,
    write_podcast_script,
)
from podcast_tts import synthesize_podcast
from source_registry import SOURCE_DEFINITIONS

logger = logging.getLogger(__name__)

MAX_ITEMS_PER_SOURCE = 8


def resolve_target_content_date(run_at=None, mode=PODCAST_TARGET_DATE_MODE):
    """根据调度时间计算播客内容日期。"""
    if run_at is None:
        run_at = datetime.now()
    if mode != "yesterday":
        raise ValueError("暂不支持的播客目标日期模式: {}".format(mode))
    return (run_at.date() - timedelta(days=1)).isoformat()


def run_podcast_generation(scheduled_time=None, output_dir=OUTPUT_ARCHIVE_DIR):
    """执行一次每日播客生成任务。"""
    if not PODCAST_ENABLED:
        logger.info("[播客] PODCAST_ENABLED=false，跳过播客生成")
        return {"status": "disabled"}

    run_at = scheduled_time if hasattr(scheduled_time, "date") else datetime.now()
    date_text = resolve_target_content_date(run_at)

    if has_successful_podcast(date_text, output_dir):
        logger.info("[播客] %s 已成功生成，跳过", date_text)
        return {"status": "skipped", "reason": "already-success", "date": date_text}

    if not acquire_podcast_lock(date_text, output_dir):
        logger.warning("[播客] %s 已有生成任务运行中，跳过", date_text)
        return {"status": "skipped", "reason": "locked", "date": date_text}

    source_count = 0
    item_count = 0
    try:
        snapshots = load_podcast_source_snapshots(date_text, output_dir)
        source_count = len(snapshots)
        item_count = sum(len(snapshot.get("items", [])) for snapshot in snapshots)
        if item_count == 0:
            raise RuntimeError("{} 没有可用于生成播客的归档内容".format(date_text))

        script = load_reusable_podcast_script(date_text, output_dir)
        if not script:
            script = build_podcast_script(date_text, snapshots)
            write_podcast_script(date_text, script, output_dir)

        tts_result = synthesize_podcast(script.get("turns", []), podcast_dir(date_text, output_dir))
        metadata = {
            "date": date_text,
            "title": script.get("title") or "{} AI 音频日报".format(date_text),
            "summary": script.get("summary", ""),
            "audio_url": "/api/podcasts/{}/podcast.mp3".format(date_text),
            "duration_seconds": tts_result.get("duration_seconds", 0),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_count": source_count,
            "item_count": item_count,
            "status": "success",
            "error": "",
            "chapters": script.get("chapters", []),
        }
        write_podcast_metadata(metadata, output_dir)
        logger.info("[播客] %s 生成完成", date_text)
        return {"status": "success", "date": date_text, "metadata": metadata}
    except Exception as e:
        logger.exception("[播客] %s 生成失败: %s", date_text, e)
        metadata = build_failed_metadata(
            date_text,
            e,
            source_count=source_count,
            item_count=item_count,
        )
        write_podcast_metadata(metadata, output_dir)
        return {"status": "failed", "date": date_text, "error": str(e)}
    finally:
        release_podcast_lock(date_text, output_dir)


def load_podcast_source_snapshots(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    """读取目标日期各来源最新归档。"""
    snapshots = []
    excluded_source_ids = _parse_source_id_list(PODCAST_EXCLUDED_SOURCE_IDS)
    for source in SOURCE_DEFINITIONS:
        source_id = source["id"]
        if source_id in excluded_source_ids:
            logger.info("[播客] 来源=%s | 日期=%s | 已配置排除", source_id, date_text)
            continue
        snapshot, served_from, batch_file = load_history_archive_snapshot(
            source_id,
            date_text,
            output_dir=output_dir,
        )
        if not snapshot:
            logger.info(
                "[播客] 来源=%s | 日期=%s | 读取自=%s | 无归档",
                source_id,
                date_text,
                served_from,
            )
            continue
        podcast_snapshot = dict(snapshot)
        podcast_snapshot["source"] = snapshot.get("source", source)
        podcast_snapshot["batch_file"] = batch_file
        podcast_snapshot["items"] = snapshot.get("items", [])[:MAX_ITEMS_PER_SOURCE]
        snapshots.append(podcast_snapshot)
    return snapshots


def _parse_source_id_list(value):
    if not value:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    return {item.strip() for item in str(value).split(",") if item.strip()}


def build_podcast_script(date_text, snapshots):
    """调用 GitHub Models，把归档资讯生成男女对话脚本。"""
    if PODCAST_SCRIPT_PROVIDER != "github_models":
        raise ValueError("暂不支持的播客脚本 provider: {}".format(PODCAST_SCRIPT_PROVIDER))
    if not GITHUB_TOKEN:
        raise RuntimeError("未配置 GITHUB_TOKEN，无法生成播客脚本")

    prompt = _build_script_prompt(date_text, snapshots)
    payload = _call_script_ai_api(prompt)
    return _normalize_script_payload(date_text, payload)


def load_reusable_podcast_script(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    """失败重跑时优先复用已生成且合法的脚本，避免重复调用模型。"""
    payload = load_podcast_script(date_text, output_dir)
    if not payload:
        return None

    try:
        script = _normalize_script_payload(date_text, payload)
    except Exception as e:
        logger.warning("[播客] %s 已有脚本不可复用，将重新生成: %s", date_text, e)
        return None

    logger.info("[播客] %s 复用已有播客脚本", date_text)
    return script


def _build_script_prompt(date_text, snapshots):
    lines = []
    for snapshot in snapshots:
        source = snapshot.get("source", {})
        source_label = source.get("label") or source.get("name") or source.get("id", "")
        lines.append("来源: {}".format(source_label))
        for index, item in enumerate(snapshot.get("items", []), 1):
            lines.append(
                "{}. 标题: {}\n   链接: {}\n   摘要: {}\n   后端关注点: {}".format(
                    index,
                    item.get("title", ""),
                    item.get("url", ""),
                    item.get("chinese_summary") or item.get("original_summary", ""),
                    item.get("backend_focus", ""),
                )
            )
        lines.append("")

    return (
        "请把以下 {} 的 AI 技术资讯改写成一段中文双人播客脚本。\n"
        "目标音频时长不超过 {} 分钟。\n"
        "整体风格：像两个熟悉 AI 基础设施和后端工程的人在录一段真实节目，"
        "不是新闻播报，也不是把摘要逐条朗读。\n"
        "要求：\n"
        "1. 保留 5 个章节：片头、开源热榜、社区讨论、官方更新、今日行动建议；"
        "章节标题可以更口语，但语义不要偏离。\n"
        "2. 每个 turns 元素只写一个角色的一小轮话，建议 1 到 3 个短句；"
        "多用追问、补充、确认、轻微转折和自然承接，避免一人连续讲很长。\n"
        "3. 不要使用模板化播报腔。尽量少写“值得关注”“从后端角度看”“今天我们看到”"
        "“接下来我们来看”“总的来说”等 AI 常见套话。\n"
        "4. 允许少量口语停顿词，例如“嗯”“对”“你看”“这里有个点”，但不要堆砌，"
        "不要写舞台说明、括号表情或音效说明。\n"
        "5. 遇到英文项目名、模型名、公司名，保留原文；不要朗读 URL，不要逐字符解释链接。\n"
        "6. 只挑最有信息密度的内容聊，允许合并同类项；听众应该能听懂为什么这条和工程实践有关。\n"
        "7. 额外生成 summary：用 50 到 100 个中文词语概括今天的热点，不要写“基于昨天”、"
        "不要写“男女对话”、不要描述生成方式。\n"
        "8. 严格返回 JSON，不要包含 Markdown。\n"
        "JSON 格式：\n"
        "{{\"title\":\"标题\",\"summary\":\"50到100个中文词语的热点总结\","
        "\"chapters\":[{{\"time\":\"00:00\",\"title\":\"今日主线\"}}],"
        "\"turns\":[{{\"role\":\"male\",\"text\":\"男声台词\"}},"
        "{{\"role\":\"female\",\"text\":\"女声台词\"}}]}}\n\n"
        "内容列表：\n{}"
    ).format(date_text, PODCAST_MAX_DURATION_MINUTES, "\n".join(lines))


def _call_script_ai_api(prompt):
    headers = {
        "Authorization": "Bearer {}".format(GITHUB_TOKEN),
        "Content-Type": "application/json",
    }
    payload = {
        "model": PODCAST_SCRIPT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个懂 AI 基础设施和后端工程的中文播客编辑。请始终返回有效 JSON。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 6000,
    }
    url = "{}/chat/completions".format(AI_API_URL)
    max_retries = max(1, PODCAST_SCRIPT_MAX_RETRIES)
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=90,
            )
            if _is_retryable_status(response.status_code) and attempt < max_retries:
                logger.warning(
                    "[播客] 脚本生成 API 临时失败 | status=%s | attempt=%d/%d",
                    response.status_code,
                    attempt,
                    max_retries,
                )
                _sleep_before_retry(attempt)
                continue

            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _parse_json_response(content)
        except requests.exceptions.RequestException as e:
            last_error = e
            if not _is_retryable_request_error(e) or attempt >= max_retries:
                raise
            logger.warning(
                "[播客] 脚本生成 API 网络异常，准备重试 | error=%s | attempt=%d/%d",
                e,
                attempt,
                max_retries,
            )
            _sleep_before_retry(attempt)

    raise last_error or RuntimeError("播客脚本生成失败")


def _is_retryable_status(status_code):
    return status_code in (429, 500, 502, 503, 504)


def _is_retryable_request_error(error):
    return isinstance(
        error,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout,
        ),
    )


def _sleep_before_retry(attempt):
    seconds = PODCAST_SCRIPT_RETRY_SECONDS * attempt
    if seconds > 0:
        time.sleep(seconds)


def _parse_json_response(content):
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _normalize_script_payload(date_text, payload):
    if not isinstance(payload, dict):
        raise ValueError("播客脚本响应不是 JSON 对象")

    turns = []
    for turn in payload.get("turns", []):
        role = turn.get("role")
        text = (turn.get("text") or "").strip()
        if role not in ("male", "female") or not text:
            continue
        turns.append({"role": role, "text": text})

    if not turns:
        raise ValueError("播客脚本没有有效台词")

    chapters = payload.get("chapters") or [
        {"time": "00:00", "title": "今日主线"},
        {"time": "01:10", "title": "开源热榜"},
        {"time": "03:20", "title": "社区讨论"},
        {"time": "05:10", "title": "官方更新"},
    ]

    return {
        "date": date_text,
        "title": payload.get("title") or "{} AI 音频日报".format(date_text),
        "summary": _normalize_summary(payload.get("summary")),
        "chapters": [
            {
                "time": str(chapter.get("time", "")),
                "title": str(chapter.get("title", "")),
            }
            for chapter in chapters
            if chapter.get("title")
        ],
        "turns": turns,
    }


def _normalize_summary(value):
    summary = " ".join(str(value or "").split())
    return summary[:220]
