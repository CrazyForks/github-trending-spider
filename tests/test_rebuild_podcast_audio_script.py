# -*- coding: utf-8 -*-
"""播客音频重合并命令行入口测试。"""

import unittest
from unittest.mock import patch

from scripts.rebuild_podcast_audio import main


class TestRebuildPodcastAudioScript(unittest.TestCase):
    def test_success_exit_code(self):
        with patch(
            "scripts.rebuild_podcast_audio.rebuild_podcast_audio",
            return_value={"status": "success"},
        ):
            self.assertEqual(main(["--date", "2026-07-21"]), 0)

    def test_failure_exit_code(self):
        with patch(
            "scripts.rebuild_podcast_audio.rebuild_podcast_audio",
            return_value={"status": "failed", "error": "boom"},
        ):
            self.assertEqual(main(["--date", "2026-07-21"]), 1)

    def test_locked_exit_code(self):
        with patch(
            "scripts.rebuild_podcast_audio.rebuild_podcast_audio",
            return_value={"status": "skipped", "reason": "locked"},
        ):
            self.assertEqual(main(["--date", "2026-07-21"]), 2)


if __name__ == "__main__":
    unittest.main()
