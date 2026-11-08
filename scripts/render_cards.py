#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Universal Card Rendering Engine for Creator Studio
--------------------------------------------------
通用科技评测/对比视频动效卡片渲染器。
支持大字金句卡、多工具横评对比卡、步骤清单卡、翻车实录卡等预设版式。
输出 1080x1920 (9:16 竖版) 高保真 PNG 及 FFmpeg 动效 MP4。
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 常用高质感色盘
COLORS = {
    "bg_dark": (15, 17, 23),         # 深曜黑
    "card_dark": (26, 29, 39),       # 卡片底色
    "card_border": (45, 50, 68),     # 边框微光
    "text_main": (245, 247, 250),    # 主文字
    "text_sub": (156, 163, 175),     # 次要灰字
    "primary": (99, 102, 241),       # 科技靛蓝
    "accent_gold": (245, 158, 11),   # 醒目金黄
    "accent_red": (239, 68, 68),     # 警示红/翻车
    "accent_green": (16, 185, 129),  # 成功绿/通过
    "brand_tag": (37, 99, 235)       # 品牌蓝
}

def get_font(size: int, bold: bool = False):
    """尝试加载系统常见中文字体，失败则回退默认"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                # PingFang index 1 or 2 is bold
                idx = 2 if bold and "PingFang" in p else 0
                return ImageFont.truetype(p, size, index=idx)
            except Exception:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
    return ImageFont.load_default()


def render_hook_card(title: str, subtitle: str, kicker: str = "实测曝光", width: int = 1080, height: int = 1920) -> Image.Image:
    """渲染 01: 黄金 3 秒大字金句/痛点抓手卡"""
    img = Image.new("RGBA", (width, height), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 顶部标签
    tag_font = get_font(36, bold=True)
    draw.rounded_rectangle([90, 320, 90 + len(kicker) * 44 + 40, 390], radius=16, fill=COLORS["brand_tag"])
    draw.text((110, 335), kicker, font=tag_font, fill=COLORS["text_main"])

    # 主大标题（支持自动换行）
    title_font = get_font(72, bold=True)
    y = 440
    # 简单的按 12 字分行
    lines = [title[i:i+11] for i in range(0, len(title), 11)]
    for line in lines:
        draw.text((90, y), line, font=title_font, fill=COLORS["text_main"])
        y += 100

    # 装饰线
    y += 20
    draw.line([90, y, width - 90, y], fill=COLORS["card_border"], width=3)
    y += 40

    # 副标题 / 痛点解释
    if subtitle:
        sub_font = get_font(42, bold=False)
        sub_lines = [subtitle[i:i+18] for i in range(0, len(subtitle), 18)]
        for sline in sub_lines:
            draw.text((90, y), sline, font=sub_font, fill=COLORS["text_sub"])
            y += 65

    # 底部卡片容器
    box_top = max(y + 60, 900)
    draw.rounded_rectangle([90, box_top, width - 90, height - 200], radius=24, fill=COLORS["card_dark"], outline=COLORS["card_border"], width=2)
    box_font = get_font(38, bold=False)
    draw.text((130, box_top + 50), "实测维度：", font=get_font(40, bold=True), fill=COLORS["accent_gold"])
    draw.text((130, box_top + 130), "• 原生版式兼容度（拒绝走样）", font=box_font, fill=COLORS["text_main"])
    draw.text((130, box_top + 200), "• 复杂图表与数据还原度", font=box_font, fill=COLORS["text_main"])
    draw.text((130, box_top + 270), "• 交付效率与返工成本", font=box_font, fill=COLORS["text_main"])

    return img


def render_comparison_card(title: str, items: list, width: int = 1080, height: int = 1920) -> Image.Image:
    """渲染 02: 多工具横向评测对比卡 (items: [{"name": "DeepSeek", "result": "套上", "note": "版式一致", "pass": True}])"""
    img = Image.new("RGBA", (width, height), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 标题
    draw.text((90, 260), title, font=get_font(64, bold=True), fill=COLORS["text_main"])
    draw.line([90, 360, width - 90, 360], fill=COLORS["card_border"], width=2)

    # 对比卡片行
    y = 400
    row_height = 240
    for idx, item in enumerate(items):
        box_rect = [90, y, width - 90, y + row_height - 30]
        # 背景
        draw.rounded_rectangle(box_rect, radius=20, fill=COLORS["card_dark"], outline=COLORS["card_border"], width=2)

        # 工具名称
        draw.text((130, y + 45), item.get("name", f"工具 {idx+1}"), font=get_font(48, bold=True), fill=COLORS["text_main"])

        # 结果标签
        is_pass = item.get("pass", True)
        badge_color = COLORS["accent_green"] if is_pass else COLORS["accent_red"]
        badge_text = item.get("result", "PASS" if is_pass else "FAIL")
        badge_w = len(badge_text) * 40 + 30
        draw.rounded_rectangle([width - 130 - badge_w, y + 40, width - 130, y + 105], radius=14, fill=badge_color)
        draw.text((width - 130 - badge_w + 15, y + 48), badge_text, font=get_font(36, bold=True), fill=COLORS["text_main"])

        # 详细说明
        note = item.get("note", "")
        draw.text((130, y + 125), note, font=get_font(34, bold=False), fill=COLORS["text_sub"])

        y += row_height

    return img


def main():
    parser = argparse.ArgumentParser(description="自媒体通用动效卡片渲染引擎")
    parser.add_argument("--type", choices=["hook", "comparison"], default="hook", help="卡片版式类型")
    parser.add_argument("--title", required=True, help="卡片主标题")
    parser.add_argument("--subtitle", default="", help="卡片副标题/说明")
    parser.add_argument("--kicker", default="实测曝光", help="顶部高亮标签")
    parser.add_argument("--items", help="对比项 JSON 字符串 (仅对比卡用)")
    parser.add_argument("--output", default="card.png", help="输出图片路径")
    parser.add_argument("--duration", type=float, default=0, help="如果 > 0，则自动调 FFmpeg 生成对应秒数的 mp4 视频")
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.type == "hook":
        img = render_hook_card(args.title, args.subtitle, args.kicker)
    elif args.type == "comparison":
        items = json.loads(args.items) if args.items else [
            {"name": "DeepSeek", "result": "套上", "note": "版式一致，数据表格未走样", "pass": True},
            {"name": "WPS 灵犀", "result": "翻车", "note": "模板风格突变，色系丢失", "pass": False},
            {"name": "Grok", "result": "翻车", "note": "吞字体，图表排版错乱", "pass": False},
            {"name": "Gemini", "result": "翻车", "note": "无法直接导出标准 pptx", "pass": False}
        ]
        img = render_comparison_card(args.title, items)

    img.save(str(out_path), "PNG")
    print(f"[+] 卡片已生成: {out_path}")

    # 如果要求生成视频
    if args.duration > 0:
        video_path = out_path.with_suffix(".mp4")
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(out_path),
            "-c:v", "libx264", "-t", str(args.duration),
            "-pix_fmt", "yuv420p", "-vf", "fps=30",
            str(video_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"[+] 视频片段已生成 ({args.duration}s): {video_path}")


if __name__ == "__main__":
    main()
