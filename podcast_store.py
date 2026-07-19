# -*- coding: utf-8 -*-
"""
每日 AI 播客文件存储、锁和只读元数据。
"""

import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from config import OUTPUT_ARCHIVE_DIR, PODCAST_HISTORY_DAYS

logger = logging.getLogger(__name__)

PODCAST_DIR_NAME = "podcasts"
PODCAST_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOCK_TTL_SECONDS = 2 * 60 * 60


def is_valid_podcast_date(date_text):
    """校验 YYYY-MM-DD 日期文本。"""
    if not PODCAST_DATE_PATTERN.match(date_text or ""):
        return False
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def podcast_root(output_dir=OUTPUT_ARCHIVE_DIR):
    return Path(output_dir) / PODCAST_DIR_NAME


def podcast_dir(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_root(output_dir) / date_text


def podcast_metadata_path(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_dir(date_text, output_dir) / "metadata.json"


def podcast_script_path(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_dir(date_text, output_dir) / "script.json"


def podcast_audio_path(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_dir(date_text, output_dir) / "podcast.mp3"


def latest_metadata_path(output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_root(output_dir) / "latest.json"


def lock_path(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    return podcast_dir(date_text, output_dir) / ".lock"


def read_json_file(path):
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.warning("读取播客 JSON 失败: %s", e)
        return None


def write_json_file(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_podcast_metadata(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    if not is_valid_podcast_date(date_text):
        return None
    return read_json_file(podcast_metadata_path(date_text, output_dir))


def load_latest_podcast_metadata(output_dir=OUTPUT_ARCHIVE_DIR):
    metadata = read_json_file(latest_metadata_path(output_dir))
    if metadata and metadata.get("status") == "success":
        return metadata

    history = list_podcast_history(
        days=max(PODCAST_HISTORY_DAYS, 30),
        output_dir=output_dir,
    )
    return history[0] if history else None


def list_podcast_history(days=PODCAST_HISTORY_DAYS, output_dir=OUTPUT_ARCHIVE_DIR, today=None):
    """按内容日期倒序列出最近 N 天成功生成的播客。"""
    if today is None:
        today = date.today()

    results = []
    for offset in range(0, days + 1):
        target_date = today - timedelta(days=offset)
        metadata = load_podcast_metadata(target_date.isoformat(), output_dir)
        if metadata and metadata.get("status") == "success":
            results.append(metadata)
        if len(results) >= days:
            break
    return results


def get_podcast_audio_file(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    if not is_valid_podcast_date(date_text):
        return None
    path = podcast_audio_path(date_text, output_dir)
    return path if path.exists() and path.is_file() else None


def has_successful_podcast(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    metadata = load_podcast_metadata(date_text, output_dir)
    return bool(metadata and metadata.get("status") == "success")


def acquire_podcast_lock(date_text, output_dir=OUTPUT_ARCHIVE_DIR, now=None, ttl_seconds=LOCK_TTL_SECONDS):
    """用独占 lock 文件避免同一天播客并发生成。"""
    if now is None:
        now = datetime.now()

    target_lock_path = lock_path(date_text, output_dir)
    target_lock_path.parent.mkdir(parents=True, exist_ok=True)

    if target_lock_path.exists():
        payload = read_json_file(target_lock_path) or {}
        expires_at = _parse_datetime(payload.get("expires_at", ""))
        if expires_at and expires_at > now:
            return False
        try:
            target_lock_path.unlink()
        except FileNotFoundError:
            pass

    payload = {
        "date": date_text,
        "locked_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds"),
    }
    try:
        fd = os.open(str(target_lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return True


def release_podcast_lock(date_text, output_dir=OUTPUT_ARCHIVE_DIR):
    try:
        lock_path(date_text, output_dir).unlink()
    except FileNotFoundError:
        pass


def write_podcast_script(date_text, script, output_dir=OUTPUT_ARCHIVE_DIR):
    write_json_file(podcast_script_path(date_text, output_dir), script)


def write_podcast_metadata(metadata, output_dir=OUTPUT_ARCHIVE_DIR):
    date_text = metadata.get("date", "")
    if not is_valid_podcast_date(date_text):
        raise ValueError("播客日期无效: {}".format(date_text))

    write_json_file(podcast_metadata_path(date_text, output_dir), metadata)
    if metadata.get("status") == "success":
        write_json_file(latest_metadata_path(output_dir), metadata)


def build_failed_metadata(date_text, error, generated_at=None, source_count=0, item_count=0):
    if generated_at is None:
        generated_at = datetime.now().isoformat(timespec="seconds")
    return {
        "date": date_text,
        "title": "{} AI 音频日报".format(date_text),
        "audio_url": "",
        "duration_seconds": 0,
        "generated_at": generated_at,
        "source_count": source_count,
        "item_count": item_count,
        "summary": "",
        "status": "failed",
        "error": str(error),
        "chapters": [],
    }


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
