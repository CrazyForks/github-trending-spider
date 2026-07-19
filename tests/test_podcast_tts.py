# -*- coding: utf-8 -*-
"""
每日 AI 播客 TTS 编排测试。
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, ".")

from podcast_tts import (  # noqa: E402
    _prepare_tts_text,
    _segment_paths_with_turn_pause,
    synthesize_podcast,
)


class TestPodcastTts(unittest.TestCase):
    def test_synthesize_podcast_uses_role_voices_and_merges(self):
        turns = [
            {"role": "male", "text": "男声台词"},
            {"role": "female", "text": "女声台词"},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("podcast_tts.PODCAST_TTS_PROVIDER", "edge_tts"), \
                    patch("podcast_tts.PODCAST_VOICE_MALE", "male-voice"), \
                    patch("podcast_tts.PODCAST_VOICE_FEMALE", "female-voice"), \
                    patch("podcast_tts.PODCAST_VOICE_MALE_RATE", "-6%"), \
                    patch("podcast_tts.PODCAST_VOICE_FEMALE_RATE", "+3%"), \
                    patch("podcast_tts.PODCAST_VOICE_MALE_PITCH", "-3Hz"), \
                    patch("podcast_tts.PODCAST_VOICE_FEMALE_PITCH", "+1Hz"), \
                    patch("podcast_tts.PODCAST_VOICE_MALE_VOLUME", "-1%"), \
                    patch("podcast_tts.PODCAST_VOICE_FEMALE_VOLUME", "+2%"), \
                    patch("podcast_tts._synthesize_edge_segment") as synthesize, \
                    patch("podcast_tts._merge_segments") as merge, \
                    patch("podcast_tts._probe_duration_seconds", return_value=123):
                result = synthesize_podcast(turns, temp_dir)

        self.assertEqual(result["duration_seconds"], 123)
        self.assertEqual(synthesize.call_args_list[0].args[1], "male-voice")
        self.assertEqual(synthesize.call_args_list[1].args[1], "female-voice")
        self.assertEqual(
            synthesize.call_args_list[0].kwargs,
            {"rate": "-6%", "pitch": "-3Hz", "volume": "-1%"},
        )
        self.assertEqual(
            synthesize.call_args_list[1].kwargs,
            {"rate": "+3%", "pitch": "+1Hz", "volume": "+2%"},
        )
        self.assertEqual(merge.call_count, 1)

    def test_prepare_tts_text_removes_urls_without_emptying_text(self):
        text = _prepare_tts_text("嗯，先看 [项目](https://example.com)，不过 URL 不用念 https://x.test/a")

        self.assertIn("项目", text)
        self.assertIn("不过", text)
        self.assertNotIn("https://", text)
        self.assertTrue(text.strip())

    def test_segment_paths_with_turn_pause_inserts_silence_between_turns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            first = target_dir / "001-male.mp3"
            second = target_dir / "002-female.mp3"

            with patch("podcast_tts.PODCAST_TURN_PAUSE_SECONDS", 0.4), \
                    patch("podcast_tts._ensure_silence_segment") as ensure_silence:
                paths = _segment_paths_with_turn_pause([first, second], target_dir)

        self.assertEqual(paths, [first, target_dir / "turn-pause.mp3", second])
        ensure_silence.assert_called_once()

    def test_empty_turns_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                synthesize_podcast([], temp_dir)


if __name__ == "__main__":
    unittest.main()
