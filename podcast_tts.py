# -*- coding: utf-8 -*-
"""
每日 AI 播客 TTS 合成。
"""

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path

from config import (
    PODCAST_TTS_PROVIDER,
    PODCAST_VOICE_FEMALE,
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
        voice = _voice_for_role(role)
        segment_path = segments_dir / "{:03d}-{}.mp3".format(index, role or "speaker")
        _synthesize_edge_segment(text, voice, segment_path)
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


def _synthesize_edge_segment(text, voice, output_path):
    async def _run():
        import edge_tts

        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(str(output_path))

    logger.info("生成播客语音片段: %s", output_path)
    asyncio.run(_run())


def _merge_segments(segment_paths, output_path):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("未找到 ffmpeg，无法合并播客音频")

    list_path = output_path.parent / "segments.txt"
    with list_path.open("w", encoding="utf-8") as f:
        for segment_path in segment_paths:
            escaped = str(segment_path.resolve()).replace("'", "'\\''")
            f.write("file '{}'\n".format(escaped))

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-acodec",
        "libmp3lame",
        "-b:a",
        "128k",
        str(output_path),
    ]
    logger.info("合并播客音频: %s", output_path)
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
