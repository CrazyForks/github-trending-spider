#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复用指定日期已有脚本和语音片段，重新合并播客音频。"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from podcast_builder import rebuild_podcast_audio  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="复用已有语音片段重新合并播客音频")
    parser.add_argument("--date", required=True, help="播客内容日期，格式 YYYY-MM-DD")
    args = parser.parse_args(argv)

    result = rebuild_podcast_audio(args.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "success":
        return 0
    if result.get("status") == "skipped":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
