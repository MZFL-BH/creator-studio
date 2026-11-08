#!/usr/bin/env python3
"""
自动静音剔除脚本 (cut_silence.py)
基于 ffmpeg 的 silencedetect 滤镜，自动扫描并切除音频中过长的思考、停顿与静音片段。

用法:
    python3 cut_silence.py --input raw_video.mp4 --output output_cut.mp4 --noise -30dB --duration 0.4
"""

import argparse
import subprocess
import re
import sys
import os

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("[错误] 未检测到 ffmpeg，请先在终端安装 (macOS: brew install ffmpeg)。", file=sys.stderr)
        sys.exit(1)

def detect_silence(input_file, noise_threshold="-30dB", duration=0.4):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-af", f"silencedetect=noise={noise_threshold}:d={duration}",
        "-f", "null", "-"
    ]
    print(f"[1/3] 正在扫描音频静音区间 (阈值: {noise_threshold}, 最小静音时长: {duration}s)...")
    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    
    silence_starts = []
    silence_ends = []
    
    for line in result.stderr.splitlines():
        if "silence_start:" in line:
            match = re.search(r"silence_start:\s*([\d\.]+)", line)
            if match:
                silence_starts.append(float(match.group(1)))
        elif "silence_end:" in line:
            match = re.search(r"silence_end:\s*([\d\.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))
                
    return list(zip(silence_starts, silence_ends))

def get_total_duration(input_file):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    return float(result.stdout.strip())

def build_keep_segments(silences, total_duration, pad=0.1):
    """
    计算保留的声音区间（pad 为气口缓冲微调，防止声音太局促导致卡顿）
    """
    keep_segments = []
    current_pos = 0.0
    
    for s_start, s_end in silences:
        seg_end = max(0.0, s_start + pad)
        if seg_end > current_pos:
            keep_segments.append((current_pos, seg_end))
        current_pos = max(current_pos, s_end - pad)
        
    if current_pos < total_duration:
        keep_segments.append((current_pos, total_duration))
        
    return keep_segments

def cut_and_merge(input_file, keep_segments, output_file):
    if not keep_segments:
        print("[提示] 未检测到明显静音段，保持原片输出。")
        return
        
    print(f"[2/3] 共保留 {len(keep_segments)} 段有声片段，正在剪切拼接...")
    
    filter_complex = []
    for idx, (start, end) in enumerate(keep_segments):
        filter_complex.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{idx}];")
        filter_complex.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{idx}];")
        
    concat_inputs = "".join([f"[v{idx}][a{idx}]" for idx in range(len(keep_segments))])
    concat_filter = f"{concat_inputs}concat=n={len(keep_segments)}:v=1:a=1[outv][outa]"
    
    full_filter = "".join(filter_complex) + concat_filter
    
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-filter_complex", full_filter,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-c:a", "aac",
        output_file
    ]
    
    print("[3/3] 正在输出剪辑文件到:", output_file)
    subprocess.run(cmd, check=True)
    print("✅ 粗剪完成！")

def main():
    parser = argparse.ArgumentParser(description="自动跳剪口播视频静音部分")
    parser.add_argument("--input", "-i", required=True, help="输入视频文件路径")
    parser.add_argument("--output", "-o", default="cut_output.mp4", help="输出视频文件路径")
    parser.add_argument("--noise", default="-30dB", help="静音音量阈值，默认 -30dB")
    parser.add_argument("--duration", type=float, default=0.4, help="判定为静音的最小秒数，默认 0.4s")
    
    args = parser.parse_args()
    check_ffmpeg()
    
    if not os.path.exists(args.input):
        print(f"[错误] 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
        
    total_len = get_total_duration(args.input)
    silences = detect_silence(args.input, args.noise, args.duration)
    keep_segments = build_keep_segments(silences, total_len)
    cut_and_merge(args.input, keep_segments, args.output)

if __name__ == "__main__":
    main()
