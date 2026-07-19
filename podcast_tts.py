# -*- coding: utf-8 -*-
"""
每日 AI 播客 TTS 合成。
"""

import asyncio
import logging
import re
import shutil
import subprocess
import time
from pathlib import Path

from config import (
    PODCAST_TURN_PAUSE_SECONDS,
    PODCAST_TTS_MAX_RETRIES,
    PODCAST_TTS_PROVIDER,
    PODCAST_TTS_RETRY_SECONDS,
    PODCAST_VOICE_FEMALE_PITCH,
    PODCAST_VOICE_FEMALE_RATE,
    PODCAST_VOICE_FEMALE_VOLUME,
    PODCAST_VOICE_FEMALE,
    PODCAST_VOICE_MALE_PITCH,
    PODCAST_VOICE_MALE_RATE,
    PODCAST_VOICE_MALE_VOLUME,
    PODCAST_VOICE_MALE,
)

logger = logging.getLogger(__name__)


def synthesize_podcast(turns, target_dir):
    """按男女角色生成音频片段，并合并成 podcast.mp3。"""
    if PODCAST_TTS_PROVIDER != "edge_tts":
        raise ValueError("暂不支持的 TTS provider: {}".format(PODCAST_TTS_PROVIDER))
    if not turns:
        raise ValueError("播客脚本为空，无法生成音频")

    target_dir = Path(target_dir)
    segments_dir = target_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    segment_paths = []
    for index, turn in enumerate(turns, 1):
        role = turn.get("role", "")
        text = (turn.get("text") or "").strip()
        if not text:
            continue
        text = _prepare_tts_text(text)
        if not text:
            continue
        voice = _voice_for_role(role)
        voice_options = _voice_options_for_role(role)
        segment_path = segments_dir / "{:03d}-{}.mp3".format(index, role or "speaker")
        _synthesize_edge_segment(text, voice, segment_path, **voice_options)
        segment_paths.append(segment_path)

    if not segment_paths:
        raise ValueError("播客脚本没有可合成文本")

    output_path = target_dir / "podcast.mp3"
    _merge_segments(segment_paths, output_path)
    return {
        "audio_path": str(output_path),
        "duration_seconds": _probe_duration_seconds(output_path),
    }


def _voice_for_role(role):
    if role == "female":
        return PODCAST_VOICE_FEMALE
    return PODCAST_VOICE_MALE


def _voice_options_for_role(role):
    if role == "female":
        return {
            "rate": PODCAST_VOICE_FEMALE_RATE,
            "pitch": PODCAST_VOICE_FEMALE_PITCH,
            "volume": PODCAST_VOICE_FEMALE_VOLUME,
        }
    return {
        "rate": PODCAST_VOICE_MALE_RATE,
        "pitch": PODCAST_VOICE_MALE_PITCH,
        "volume": PODCAST_VOICE_MALE_VOLUME,
    }


def _prepare_tts_text(text):
    """清理不适合朗读的内容，并用标点制造更自然的短停顿。"""
    original = " ".join(str(text or "").split())
    if not original:
        return ""

    cleaned = original
    cleaned = re.sub(r"\[[^\]]+\]\([^)]+\)", lambda m: m.group(0).split("]")[0][1:], cleaned)
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    cleaned = cleaned.replace("；", "，").replace(";", "，")
    cleaned = re.sub(r"[。！？!?]{2,}", lambda m: m.group(0)[0], cleaned)
    cleaned = re.sub(r"([。！？!?])(?=\S)", r"\1 ", cleaned)
    cleaned = re.sub(r"(?<![，。！？!?])(不过|但是|所以|另外|这里|换句话说|也就是说)", r"，\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ，")
    return cleaned or original


def _synthesize_edge_segment(text, voice, output_path, rate="+0%", pitch="+0Hz", volume="+0%"):
    max_retries = max(1, PODCAST_TTS_MAX_RETRIES)
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            _synthesize_edge_segment_once(text, voice, output_path, rate, pitch, volume)
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise RuntimeError("TTS 生成了空音频文件")
            return
        except Exception as e:
            last_error = e
            _remove_empty_or_partial_file(output_path)
            if attempt >= max_retries:
                logger.error(
                    "播客语音片段生成失败 | voice=%s | text=%s | error=%s",
                    voice,
                    text[:40],
                    e,
                )
                raise
            logger.warning(
                "播客语音片段生成失败，准备重试 | voice=%s | attempt=%d/%d | text=%s | error=%s",
                voice,
                attempt,
                max_retries,
                text[:40],
                e,
            )
            _sleep_before_tts_retry(attempt)

    raise last_error


def _synthesize_edge_segment_once(text, voice, output_path, rate, pitch, volume):
    async def _run():
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        await communicate.save(str(output_path))

    logger.info("生成播客语音片段: %s", output_path)
    asyncio.run(_run())


def _remove_empty_or_partial_file(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass


def _sleep_before_tts_retry(attempt):
    seconds = PODCAST_TTS_RETRY_SECONDS * attempt
    if seconds > 0:
        time.sleep(seconds)


def _merge_segments(segment_paths, output_path):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("未找到 ffmpeg，无法合并播客音频")

    merge_paths = _segment_paths_with_turn_pause(segment_paths, output_path.parent)
    list_path = output_path.parent / "segments.txt"
    with list_path.open("w", encoding="utf-8") as f:
        for segment_path in merge_paths:
            escaped = str(segment_path.resolve()).replace("'", "'\\''")
            f.write("file '{}'\n".format(escaped))

    raw_output_path = output_path.with_name("{}-raw{}".format(output_path.stem, output_path.suffix))
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "128k",
        str(raw_output_path),
    ]
    logger.info("合并播客音频: %s", output_path)
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_output_path.replace(output_path)


def _segment_paths_with_turn_pause(segment_paths, target_dir):
    if PODCAST_TURN_PAUSE_SECONDS <= 0 or len(segment_paths) <= 1:
        return segment_paths

    silence_path = Path(target_dir) / "turn-pause.mp3"
    _ensure_silence_segment(silence_path, PODCAST_TURN_PAUSE_SECONDS)

    merge_paths = []
    for index, segment_path in enumerate(segment_paths):
        merge_paths.append(segment_path)
        if index < len(segment_paths) - 1:
            merge_paths.append(silence_path)
    return merge_paths


def _ensure_silence_segment(output_path, duration_seconds):
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=32000:cl=mono",
        "-t",
        "{:.3f}".format(max(0.05, duration_seconds)),
        "-acodec",
        "libmp3lame",
        "-b:a",
        "128k",
        str(output_path),
    ]
    logger.info("生成播客转场静音: %s", output_path)
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _probe_duration_seconds(audio_path):
    if not shutil.which("ffprobe"):
        return 0

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return int(float(result.stdout.strip() or "0"))
    except Exception as e:
        logger.warning("读取播客时长失败: %s", e)
        return 0
