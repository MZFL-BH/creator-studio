#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Assembly Tool for Creator Studio
--------------------------------------
根据分镜清单或指定目录，将动效卡片视频与出镜占位片段快速缝合成一条完整的草稿样片。
标准化输出 1080x1920 30fps H.264 视频。
"""

import os
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path


def assemble_clips(clip_paths: list, output_path: Path):
    """通过 FFmpeg concat demuxer 快速拼接视频片段"""
    if not clip_paths:
        print("[-] 错误：没有提供待拼接的视频片段。")
        return False

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for clip in clip_paths:
            f.write(f"file '{Path(clip).resolve()}'\n")
        concat_list = f.name

    try:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            str(output_path.resolve())
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[√] 视频拼接完成: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] FFmpeg 拼接失败: {e}")
        return False
    finally:
        if os.path.exists(concat_list):
            os.remove(concat_list)


def main():
    parser = argparse.ArgumentParser(description="视频片段快速拼接装配器")
    parser.add_argument("clips", nargs="*", help="待拼接的视频片段列表（按播放顺序）")
    parser.add_argument("--dir", help="如果传入目录，则按自然排序拼接该目录下所有 mp4")
    parser.add_argument("--output", "-o", default="draft-silent.mp4", help="输出视频路径")
    args = parser.parse_args()

    clip_list = []
    if args.dir:
        dir_path = Path(args.dir).resolve()
        clip_list = sorted(list(dir_path.glob("*.mp4")))
    elif args.clips:
        clip_list = [Path(c) for c in args.clips]

    if not clip_list:
        print("[-] 请指定待拼接的视频文件或使用 --dir 指定目录。")
        sys.exit(1)

    print(f"[*] 准备拼接 {len(clip_list)} 个视频片段...")
    assemble_clips(clip_list, Path(args.output))


if __name__ == "__main__":
    main()
