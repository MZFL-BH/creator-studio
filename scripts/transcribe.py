#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creator Studio · 极客音视频抓取与转写引擎 (Rip & Transcribe Engine)
===================================================================
深度融合三大生产力神器：yt-dlp + OpenAI Whisper + FFmpeg
解决自媒体两大痛点：
1. [对标秒级拆解] 一键下载 B站/抖音/油管对标视频，Whisper 毫秒级转写文案并提炼黄金 Hook 与节奏
2. [本地自动打轴] 录完口播无需手打字幕，Whisper 自动生成 .srt 字幕，FFmpeg 极速封装字幕轨
"""

import os
import sys
import json
import re
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# 自动发现本地关键工具路径
def find_binary(name, candidate_paths=None):
    # 优先环境变量
    found = shutil.which(name)
    if found:
        return found
    if candidate_paths:
        for p in candidate_paths:
            if Path(p).exists() and os.access(p, os.X_OK):
                return str(p)
    return None

YTDLP_BIN = find_binary("yt-dlp", [
    Path.home() / ".agent-reach-venv-311" / "bin" / "yt-dlp",
    "/opt/homebrew/bin/yt-dlp",
    "/usr/local/bin/yt-dlp"
])

WHISPER_BIN = find_binary("whisper", [
    Path.home() / "anaconda3" / "bin" / "whisper",
    "/opt/homebrew/bin/whisper",
    "/usr/local/bin/whisper"
])

FFMPEG_BIN = find_binary("ffmpeg", [
    Path.home() / ".gemini" / "antigravity" / "bin" / "ffmpeg",
    "/opt/homebrew/bin/ffmpeg",
    Path.home() / "anaconda3" / "bin" / "ffmpeg"
])


def setup_proxy_env():
    """若检测到本地 127.0.0.1:7890 代理存活，自动注入环境变量加速网络请求"""
    env = os.environ.copy()
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex(('127.0.0.1', 7890))
        s.close()
        if res == 0:
            env["http_proxy"] = "http://127.0.0.1:7890"
            env["https_proxy"] = "http://127.0.0.1:7890"
            env["HTTP_PROXY"] = "http://127.0.0.1:7890"
            env["HTTPS_PROXY"] = "http://127.0.0.1:7890"
    except Exception:
        pass
    return env


def is_url(target: str) -> bool:
    """判断输入是否为网络链接"""
    return target.startswith("http://") or target.startswith("https://") or "v.douyin.com" in target or "bilibili.com" in target or "youtube.com" in target or "youtu.be" in target


def clean_douyin_url(raw_text: str) -> str:
    """从抖音分享口令中清洗提取标准链接"""
    m = re.search(r'https?://[^\s]+', raw_text)
    return m.group(0) if m else raw_text.strip()


def download_media(url: str, output_dir: Path, audio_only: bool = False) -> Path:
    """调用 yt-dlp 抓取视频或音频"""
    if not YTDLP_BIN:
        raise RuntimeError("未检测到 yt-dlp，请确认已安装并在 PATH 中。")

    output_dir.mkdir(parents=True, exist_ok=True)
    clean_url = clean_douyin_url(url)
    print(f"[*] 启动 yt-dlp 下载目标: {clean_url}")

    env = setup_proxy_env()
    out_template = str(output_dir / "%(title)s_%(id)s.%(ext)s")

    cmd = [YTDLP_BIN, "--no-playlist", "-o", out_template]
    if audio_only:
        cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
    else:
        # 下载最高画质 MP4
        cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])

    cmd.append(clean_url)
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        # 降级尝试更宽松格式
        print(f"[-] 默认格式重试，降级抓取中...")
        cmd_fallback = [YTDLP_BIN, "--no-playlist", "-o", out_template, clean_url]
        proc = subprocess.run(cmd_fallback, env=env, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"yt-dlp 下载失败: {proc.stderr[:300]}")

    # 寻找最新落盘的文件
    files = sorted(output_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise RuntimeError("yt-dlp 执行成功但未找到产物文件。")
    return files[0]


def extract_audio_16k(video_path: Path, output_wav: Path) -> Path:
    """调用 FFmpeg 将音视频转换为 Whisper 原生最爱的 16kHz 单声道 WAV，大幅提升推理速度"""
    if not FFMPEG_BIN:
        return video_path
    cmd = [
        FFMPEG_BIN, "-y", "-i", str(video_path),
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(output_wav)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_wav


def transcribe(audio_path: Path, output_dir: Path, model: str = "base", language: str = "zh") -> dict:
    """调用 OpenAI Whisper CLI 进行毫秒级转写与打轴"""
    if not WHISPER_BIN:
        raise RuntimeError("未检测到 whisper CLI，请检查 Anaconda 或 Python 环境。")

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] 启动 Whisper ({model} 模型) 本地转写 -> {audio_path.name}...")

    env = setup_proxy_env()
    cmd = [
        WHISPER_BIN, str(audio_path),
        "--model", model,
        "--output_dir", str(output_dir),
        "--output_format", "all"
    ]
    if language:
        cmd.extend(["--language", language])

    # 执行转写
    start_time = datetime.now()
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Whisper 转写失败: {proc.stderr[:300]}")
    cost_sec = (datetime.now() - start_time).total_seconds()

    stem = audio_path.stem
    txt_file = output_dir / f"{stem}.txt"
    srt_file = output_dir / f"{stem}.srt"

    full_text = txt_file.read_text(encoding="utf-8").strip() if txt_file.exists() else ""

    # 计算语速与统计
    char_count = len(re.sub(r'\s+', '', full_text))

    return {
        "txt_file": txt_file,
        "srt_file": srt_file,
        "full_text": full_text,
        "char_count": char_count,
        "cost_seconds": cost_sec
    }


def embed_subtitles_to_mp4(video_path: Path, srt_path: Path, output_mp4: Path) -> bool:
    """使用 FFmpeg 将 SRT 封装进 MP4 软字幕轨（零重编码损失）"""
    if not FFMPEG_BIN or not video_path.exists() or not srt_path.exists():
        return False
    print(f"[*] 正在将字幕轨封装进 MP4: {output_mp4.name}...")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(video_path),
        "-i", str(srt_path),
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=chi",
        str(output_mp4)
    ]
    proc = subprocess.run(cmd, capture_output=True)
    return proc.returncode == 0


def analyze_transcript(full_text: str, duration_sec: float = 0.0) -> dict:
    """对文案进行自媒体网感与结构拆解"""
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    if not lines:
        lines = [full_text]

    # 黄金 3 秒 Hook：取前两句话
    first_few = re.split(r'[。！？\n]', full_text)
    hook = "。".join([s.strip() for s in first_few[:2] if s.strip()]) + "。"

    return {
        "hook": hook,
        "lines_count": len(lines),
        "preview": full_text[:280] + ("..." if len(full_text) > 280 else "")
    }


def main():
    parser = argparse.ArgumentParser(description="Creator Studio · 极客音视频抓取与 Whisper 转写打轴引擎")
    parser.add_argument("target", help="网络视频链接 (B站/抖音/YouTube) 或 本地音视频文件路径")
    parser.add_argument("-o", "--output-dir", default="", help="产物输出目录 (默认当前目录或同级输出)")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "turbo"], help="Whisper 模型规格 (默认 base，兼顾速度与准确度)")
    parser.add_argument("--audio-only", action="store_true", help="抓取网络链接时仅下载高质量音频 (极速)")
    parser.add_argument("--embed", action="store_true", help="转写完成后使用 FFmpeg 将字幕轨封装进 MP4")
    parser.add_argument("--lang", default="zh", help="目标语言 (默认 zh 中文)")
    args = parser.parse_args()

    target = args.target.strip()
    is_network = is_url(target)

    # 确定输出目录
    if args.output_dir:
        out_dir = Path(args.output_dir).resolve()
    else:
        out_dir = Path.cwd() / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 68)
    print(f"🎬 Creator Studio · 音视频扒取与打轴工作流")
    print(f"• yt-dlp:  {YTDLP_BIN or '未找到'}")
    print(f"• Whisper: {WHISPER_BIN or '未找到'}")
    print(f"• FFmpeg:  {FFMPEG_BIN or '未找到'}")
    print("=" * 68)

    local_media = None

    # 1. 网络下载阶段
    if is_network:
        try:
            local_media = download_media(target, out_dir, audio_only=args.audio_only)
            print(f"[√] 媒体抓取成功: {local_media.name} ({local_media.stat().st_size / 1024 / 1024:.2f} MB)")
        except Exception as e:
            print(f"[-] 下载失败: {e}")
            return
    else:
        local_media = Path(target).resolve()
        if not local_media.exists():
            print(f"[-] 本地文件不存在: {local_media}")
            return

    # 2. 音频提取加速预处理 (16kHz 单声道)
    wav_cache = out_dir / f"{local_media.stem}_16k.wav"
    try:
        extract_audio_16k(local_media, wav_cache)
        transcribe_input = wav_cache
    except Exception:
        transcribe_input = local_media

    # 3. Whisper 本地转写打轴
    try:
        result = transcribe(transcribe_input, out_dir, model=args.model, language=args.lang)
        # 清理 16k 缓存音频
        if wav_cache.exists():
            wav_cache.unlink()

        # 4. 文案网感分析与结构提炼
        analysis = analyze_transcript(result["full_text"])

        print("\n" + "=" * 68)
        print(f"🎯 Whisper 转写与打轴大功告成！(耗时: {result['cost_seconds']:.1f} 秒)")
        print(f"• 字数统计:   共 {result['char_count']} 字")
        print(f"• 字幕产物:   {result['srt_file']}")
        print(f"• 全文文稿:   {result['txt_file']}")
        print("-" * 68)
        print(f"💡 提炼黄金 Hook: {analysis['hook']}")
        print("-" * 68)
        print(f"📝 文稿节选前瞻:\n{analysis['preview']}")
        print("=" * 68)

        # 5. 可选软字幕封装
        if args.embed and local_media.suffix.lower() == ".mp4" and result["srt_file"].exists():
            subtitled_video = out_dir / f"{local_media.stem}_subtitled.mp4"
            if embed_subtitles_to_mp4(local_media, result["srt_file"], subtitled_video):
                print(f"[🎉] 已将软字幕封装进成片: {subtitled_video.name}")

    except Exception as e:
        print(f"[-] 转写失败: {e}")


if __name__ == "__main__":
    main()
