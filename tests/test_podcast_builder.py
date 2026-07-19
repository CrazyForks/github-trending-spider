# -*- coding: utf-8 -*-
"""
每日 AI 播客生成编排测试。
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, ".")

from podcast_builder import (  # noqa: E402
    load_podcast_source_snapshots,
    resolve_target_content_date,
    run_podcast_generation,
)
from podcast_store import load_podcast_metadata, write_podcast_metadata  # noqa: E402


class TestPodcastBuilder(unittest.TestCase):
    def _write_archive(self, root, source_id="github-daily", date_text="2026-07-19"):
        target_dir = Path(root) / source_id / date_text
        target_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": "{}T23:50:00".format(date_text),
            "source": {"id": source_id, "label": "GitHub 日榜"},
            "item_count": 1,
            "items": [
                {
                    "title": "AI infra project",
                    "url": "https://example.com/ai",
                    "chinese_summary": "一个 AI 基础设施项目。",
                    "backend_focus": "关注队列、缓存和可观测性。",
                }
            ],
        }
        with (target_dir / "01.json").open("w", encoding="utf-8") as f:
            json.dump(payload, f)

    def test_target_content_date_uses_yesterday(self):
        run_at = datetime(2026, 7, 20, 2, 30, 0)

        self.assertEqual(resolve_target_content_date(run_at), "2026-07-19")

    def test_existing_success_metadata_skips_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_podcast_metadata(
                {
                    "date": "2026-07-19",
                    "title": "done",
                    "audio_url": "/api/podcasts/2026-07-19/podcast.mp3",
                    "duration_seconds": 1,
                    "generated_at": "2026-07-20T02:30:00",
                    "source_count": 1,
                    "item_count": 1,
                    "status": "success",
                    "error": "",
                    "chapters": [],
                },
                output_dir=temp_dir,
            )

            with patch("podcast_builder.PODCAST_ENABLED", True):
                result = run_podcast_generation(
                    scheduled_time=datetime(2026, 7, 20, 2, 30, 0),
                    output_dir=temp_dir,
                )

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "already-success")

    def test_no_archive_writes_failed_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("podcast_builder.PODCAST_ENABLED", True):
                result = run_podcast_generation(
                    scheduled_time=datetime(2026, 7, 20, 2, 30, 0),
                    output_dir=temp_dir,
                )

            metadata = load_podcast_metadata("2026-07-19", output_dir=temp_dir)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(metadata["status"], "failed")
            self.assertEqual(metadata["item_count"], 0)

    def test_load_source_snapshots_excludes_configured_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self._write_archive(temp_dir, source_id="github-daily")
            self._write_archive(temp_dir, source_id="tldr-ai")
            self._write_archive(temp_dir, source_id="infoq")

            snapshots = load_podcast_source_snapshots("2026-07-19", output_dir=temp_dir)

            source_ids = [snapshot["source"]["id"] for snapshot in snapshots]
            self.assertIn("github-daily", source_ids)
            self.assertNotIn("tldr-ai", source_ids)
            self.assertNotIn("infoq", source_ids)

    def test_successful_generation_writes_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self._write_archive(temp_dir)
            script = {
                "title": "2026-07-19 AI 音频日报",
                "chapters": [{"time": "00:00", "title": "今日主线"}],
                "turns": [
                    {"role": "male", "text": "今天先看开源热榜。"},
                    {"role": "female", "text": "这个项目和后端工程很相关。"},
                ],
            }

            with patch("podcast_builder.PODCAST_ENABLED", True), \
                    patch("podcast_builder.build_podcast_script", return_value=script), \
                    patch("podcast_builder.synthesize_podcast", return_value={"duration_seconds": 123}):
                result = run_podcast_generation(
                    scheduled_time=datetime(2026, 7, 20, 2, 30, 0),
                    output_dir=temp_dir,
                )

            metadata = load_podcast_metadata("2026-07-19", output_dir=temp_dir)
            self.assertEqual(result["status"], "success")
            self.assertEqual(metadata["status"], "success")
            self.assertEqual(metadata["duration_seconds"], 123)
            self.assertEqual(metadata["source_count"], 1)
            self.assertEqual(metadata["item_count"], 1)


if __name__ == "__main__":
    unittest.main()
