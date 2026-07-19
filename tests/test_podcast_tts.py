# -*- coding: utf-8 -*-
"""
每日 AI 播客 TTS 编排测试。
"""

import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, ".")

from podcast_tts import synthesize_podcast  # noqa: E402


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
                    patch("podcast_tts._synthesize_edge_segment") as synthesize, \
                    patch("podcast_tts._merge_segments") as merge, \
                    patch("podcast_tts._probe_duration_seconds", return_value=123):
                result = synthesize_podcast(turns, temp_dir)

        self.assertEqual(result["duration_seconds"], 123)
        self.assertEqual(synthesize.call_args_list[0].args[1], "male-voice")
        self.assertEqual(synthesize.call_args_list[1].args[1], "female-voice")
        self.assertEqual(merge.call_count, 1)

    def test_empty_turns_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                synthesize_podcast([], temp_dir)


if __name__ == "__main__":
    unittest.main()
