#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creator Studio · 全自动自媒体出片流水线总控 (Pipeline Master)
===========================================================
将 ffmpeg-skill、oil-cover、feishu_sync 与本地卡片引擎无缝串联：
1. [音频/粗剪] 调用 ffmpeg-skill 自动剔除气口停顿、LUFS 响度平衡(-14dB)
2. [封面方案] 调用 oil-cover 自动截取 8 张高质感候选帧 + 规划小红书(3:4)/B站(4:3)封面
3. [云端看板] 调用 feishu_sync 自动将当前工程与物料状态同步入库飞书多维表格
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

SKILL_ROOT = Path("/Users/wangbinghao/.gemini/config/skills")
FFMPEG_SKILL_DIR = SKILL_ROOT / "ffmpeg-skill" / "scripts"
OIL_COVER_SCRIPT = SKILL_ROOT / "oil-cover" / "scripts" / "generate_oil_cover.py"
FEISHU_SYNC_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "feishu_sync.py"
RENDER_CARDS_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "render_cards.py"
ASSEMBLE_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "assemble_video.py"
REVIEW_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "review.py"
GENERATE_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "generate_script.py"


def run_cmd(cmd, desc=""):
    if desc:
        print(f"[*] {desc}...")
    proc = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip()
        print(f"[-] 警告/跳过: {err[:300]}")
        return False
    return True


def process_project(dir_path: Path, skip_audio: bool = False, skip_cover: bool = False, skip_sync: bool = False):
    dir_path = dir_path.resolve()
    print(f"\n=======================================================")
    print(f"🎬 启动流水线作业: {dir_path.name}")
    print(f"=======================================================")

    # 1. 寻找核心视频文件
    videos = list(dir_path.glob("*.mp4")) + list((dir_path / "delivery").glob("*.mp4") if (dir_path / "delivery").exists() else [])
    # 优先找 final 或 draft
    main_video = None
    for v in sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True):
        if not v.name.endswith("_tight.mp4") and not v.name.endswith("_loudnorm.mp4"):
            main_video = v
            break

    # 2. [环节一：音频与剪辑优化 (ffmpeg-skill)]
    if not skip_audio and main_video and FFMPEG_SKILL_DIR.exists():
        # A. 响度归一化 (LUFS -14dB)
        norm_video = main_video.with_name(f"{main_video.stem}_loudnorm.mp4")
        if not norm_video.exists():
            cmd = [
                sys.executable, str(FFMPEG_SKILL_DIR / "loudness.py"),
                str(main_video), "-o", str(norm_video), "--overwrite"
            ]
            if run_cmd(cmd, f"执行音频标准化 (-14 LUFS 响度对齐) -> {main_video.name}"):
                print(f"[√] 音频响度优化完成: {norm_video.name}")
        else:
            print(f"[i] 已存在标准化音频版本: {norm_video.name}")

        # B. 寻找原始口播音频或出镜视频做静音气口切除
        raw_clips = list(dir_path.glob("raw_*.mp4")) + list(dir_path.glob("*talking_head*.mp4"))
        for raw in raw_clips:
            tight_clip = raw.with_name(f"{raw.stem}_tight.mp4")
            if not tight_clip.exists():
                cmd = [
                    sys.executable, str(FFMPEG_SKILL_DIR / "silence.py"),
                    str(raw), "-o", str(tight_clip), "--threshold", "-35", "--min-silence", "0.6", "--hw"
                ]
                if run_cmd(cmd, f"智能切除停顿气口 -> {raw.name}"):
                    print(f"[√] 口播去静音完成: {tight_clip.name}")

    # 3. [环节二：智能封面选帧与方案规划 (oil-cover)]
    target_video = main_video
    if not skip_cover and target_video and OIL_COVER_SCRIPT.exists():
        cover_out_dir = dir_path / f"{target_video.stem}.oil-cover"
        # 提取标题
        title = dir_path.name
        script_file = next(dir_path.glob("*脚本*.md"), None) or next(dir_path.glob("*script*.md"), None)
        if script_file:
            try:
                for line in script_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
            except Exception:
                pass

        cmd = [
            sys.executable, str(OIL_COVER_SCRIPT),
            "--video", str(target_video),
            "--title", title,
            "--dry-run"
        ]
        if run_cmd(cmd, f"调用 oil-cover 从视频截取关键帧与生成封面方案 ({target_video.name})"):
            print(f"[√] 封面候选帧与排版已就绪: {cover_out_dir.name}/ (包含 3:4 与 4:3 方案)")

    # 4. [环节三：同步飞书多维表格 (feishu_sync)]
    if not skip_sync and FEISHU_SYNC_SCRIPT.exists():
        cmd = [sys.executable, str(FEISHU_SYNC_SCRIPT), str(dir_path)]
        if run_cmd(cmd, "同步物料资产与进度至飞书多维表格"):
            print(f"[√] 飞书多维表格同步成功！")

    print(f"\n[🎉] 流水线执行完毕！工程目录: {dir_path}\n")


def main():
    parser = argparse.ArgumentParser(description="自媒体全链路流水线总控 (Pipeline Master)")
    parser.add_argument("target", nargs="?", default=".", help="目标选题工程目录（默认当前目录）")
    parser.add_argument("--scan", action="store_true", help="扫描素材库所有子目录批量作业")
    parser.add_argument("--skip-audio", action="store_true", help="跳过音频响度/去静音步骤")
    parser.add_argument("--skip-cover", action="store_true", help="跳过封面选帧规划步骤")
    parser.add_argument("--skip-sync", action="store_true", help="跳过飞书表格同步步骤")
    parser.add_argument("--init-script", type=str, help="初始化新选题的10分钟爆款脚本与多平台文案 (传入选题名称)")
    parser.add_argument("--review", action="store_true", help="在出片流程后执行数据复盘与体检诊断 (review.py)")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()

    if args.init_script:
        if GENERATE_SCRIPT.exists():
            cmd = [sys.executable, str(GENERATE_SCRIPT), args.init_script, "-o", str(target_path)]
            subprocess.run(cmd)
        else:
            print("[-] 未找到 generate_script.py 脚本。")
        return

    if args.review:
        if REVIEW_SCRIPT.exists():
            cmd = [sys.executable, str(REVIEW_SCRIPT), str(target_path)]
            subprocess.run(cmd)
        else:
            print("[-] 未找到 review.py 脚本。")
        return

    if args.scan:
        print(f"[*] 批量扫描素材库: {target_path}")
        subdirs = sorted([d for d in target_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
        for d in subdirs:
            # 只有含脚本或视频的才处理
            has_script = any(d.glob("*脚本*.md")) or any(d.glob("*script*.md"))
            has_video = any(d.glob("*.mp4"))
            if has_script or has_video:
                process_project(d, args.skip_audio, args.skip_cover, args.skip_sync)
    else:
        process_project(target_path, args.skip_audio, args.skip_cover, args.skip_sync)


if __name__ == "__main__":
    main()
