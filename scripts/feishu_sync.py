#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feishu Bitable Sync Tool for Creator Studio
-------------------------------------------
自动解析本地自媒体选题工程目录，将标题、分镜状态、核心痛点、产物清单与素材路径
一键无缝同步至飞书多维表格「AI自媒体自动化·选题与出片总表」。

支持单目录同步与全量素材目录扫描同步。
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path

# 默认飞书多维表格配置
FEISHU_BASE_URL = "https://my.feishu.cn/base/KWl2bUe9fa5CKvsctVjcSb59nVb?table=tblKLLxJdPltUSA5&view=vewgDwbRSG"
DEFAULT_SPACE_NAME = "feishu-sync-space"
DEFAULT_PROFILE_ID = "Profile 3"

FIELD_IDS = {
    "title": "fldMBxOfhS",        # 选题标题 (Text)
    "status": "fldDnDxtyr",       # 流程状态 (Single Select)
    "ref_link": "fldorZE7Oc",     # 对标参考链接 (URL)
    "hook": "fldw722Mbu",         # 核心爆点/痛点 (Text)
    "path": "fld3sPw8TB",         # 本地素材路径 (Text)
    "assets": "fldXDDYDhM",       # 成片与文案 (Text)
    "platforms": "fldJoy3bbJ",    # 分发平台 (Multi Select)
    "views": "fldWqEuIEh"         # 全网播放数据 (Number)
}


def parse_project_dir(dir_path: Path) -> dict:
    """解析单个视频工程目录的元信息与产物状态"""
    dir_path = dir_path.resolve()
    if not dir_path.is_dir():
        return None

    dir_name = dir_path.name
    # 过滤非工程目录（如隐藏目录、纯封面图库、通用辅助文件夹）
    if dir_name.startswith(".") or dir_name in ["封面合集", "品牌资产", "other", "grokbot-ui-shots", "剪辑提升", "剪辑精进"]:
        return None

    # 1. 寻找脚本文件
    script_candidates = list(dir_path.glob("*脚本*.md")) + list(dir_path.glob("*script*.md"))
    script_file = script_candidates[0] if script_candidates else None

    # 2. 寻找发布文案
    publish_candidates = list(dir_path.glob("*发布*.md")) + list(dir_path.glob("publish*.md")) + list(dir_path.glob("04-小红书*.md"))
    publish_file = publish_candidates[0] if publish_candidates else None

    # 3. 寻找口播字幕
    voice_candidates = list(dir_path.glob("voiceover*.txt")) + list(dir_path.glob("*字幕*.md")) + list(dir_path.glob("*字幕*.txt"))
    voice_file = voice_candidates[0] if voice_candidates else None

    # 4. 寻找视频产物
    videos = list(dir_path.glob("*.mp4")) + list((dir_path / "delivery").glob("*.mp4") if (dir_path / "delivery").exists() else [])
    video_names = [v.name for v in videos]

    # 没有脚本且没有视频的目录大概率不是视频工程
    if not script_file and not videos:
        return None

    # --- 提炼选题标题 ---
    title = ""
    hook = ""
    if script_file and script_file.exists():
        try:
            content = script_file.read_text(encoding="utf-8")
            # 提取第一个 # 一级标题
            h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            
            # 提取黄金 3 秒 / Hook / 痛点
            hook_match = re.search(r"(?:HOOK|出镜 ①|开头|痛点).*?\n(?:.*?\n){0,3}?(?:口播|台词)[:：]\s*(.+)", content)
            if hook_match:
                hook = hook_match.group(1).strip()
            elif h1_match:
                # 备选提取正文首段有实质内容的文字
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and not p.strip().startswith("#")]
                if paragraphs:
                    hook = paragraphs[0][:150].replace("\n", " ")
        except Exception:
            pass

    # 若未提取到标题，回退使用目录名清洗版
    if not title:
        # 去掉如 20261030- 前缀
        clean_name = re.sub(r"^\d{4,8}-?", "", dir_name)
        title = clean_name.strip() or dir_name

    # --- 判定流程状态 ---
    # 状态池: 待确认 | 脚本已出 | 待录制出镜 | 成片已渲染 | 已分发
    status = "待确认"
    has_final_video = any(re.search(r"(final|v\d+).*\.mp4", v, re.IGNORECASE) for v in video_names)
    has_silent_draft = any("silent" in v.lower() for v in video_names) or (dir_path / "NEXT-FOR-ETHAN.md").exists()
    has_published_flag = (dir_path / "08-发布检查清单.md").exists() or (dir_path / "published.flag").exists()

    if has_published_flag:
        status = "已分发"
    elif has_final_video:
        status = "成片已渲染"
    elif has_silent_draft:
        status = "待录制出镜"
    elif script_file:
        status = "脚本已出"

    # --- 产物文件清单汇总 ---
    asset_list = []
    if script_file:
        asset_list.append(script_file.name)
    if publish_file:
        asset_list.append(publish_file.name)
    if voice_file:
        asset_list.append(voice_file.name)
    for v in video_names[:2]:
        asset_list.append(v)
    if len(video_names) > 2:
        asset_list.append(f"+{len(video_names)-2}个视频")

    covers = list(dir_path.glob("封面*.png")) + list(dir_path.glob("*封面*.png"))
    if covers:
        asset_list.append(f"封面({len(covers)}张)")

    assets_str = ", ".join(asset_list)

    # 默认分发平台
    platforms = ["B站", "小红书", "抖音", "视频号"]

    return {
        "title": title,
        "status": status,
        "ref_link": "",
        "hook": hook[:200] if hook else "针对目标用户核心工作流的痛点实测与效率对比",
        "path": str(dir_path),
        "assets": assets_str,
        "platforms": platforms,
        "views": 0
    }


def sync_record_via_browser(record: dict) -> bool:
    """通过 ego-browser 调用已登录的飞书会话，将记录提交到多维表格"""
    node_script = f"""
let task;
try {{
    task = await taskSpace("{DEFAULT_SPACE_NAME}", {{ profileId: "{DEFAULT_PROFILE_ID}" }});
}} catch (e) {{
    if (e.message && e.message.includes("already exists")) {{
        task = await taskSpace("{DEFAULT_SPACE_NAME}");
    }} else {{
        throw e;
    }}
}}
const page = task.page("p1");

const record = {json.dumps(record, ensure_ascii=False)};

// 1. 确保在目标表格页面
const currentUrl = await page.url();
if (!currentUrl.includes("KWl2bUe9fa5CKvsctVjcSb59nVb")) {{
    console.log("Navigating to Bitable...");
    await page.goto("{FEISHU_BASE_URL}", {{ waitUntil: "domcontentloaded", timeout: 30000 }});
    await page.waitForTimeout(4000);
}}

// 2. 清理残余遮罩/抽屉
await page.evaluate(() => {{
    const closeBtn = document.querySelector('.bitable-card-modal-header-v2-btn-close');
    if (closeBtn) closeBtn.click();
    const mask = document.querySelector('.bitable-drawer-card-mask');
    if (mask) mask.click();
}});
await page.waitForTimeout(500);

// 3. 点击「添加记录」
console.log("Opening Add Record modal...");
await page.click('.bitable-add-record-toolbar-button__main');
await page.waitForTimeout(1500);

// 辅助方法：填充 Slate 编辑器字段
async function fillField(fieldId, text) {{
    if (!text) return;
    const selector = `[data-field-id="${{fieldId}}"] [contenteditable="true"]`;
    const exists = await page.evaluate((sel) => !!document.querySelector(sel), selector);
    if (exists) {{
        await page.click(selector);
        await page.waitForTimeout(100);
        await page.keyboard.press('Meta+A');
        await page.keyboard.press('Backspace');
        await page.keyboard.type(text);
        await page.waitForTimeout(200);
    }}
}}

// 4. 填充 选题标题
await fillField("{FIELD_IDS['title']}", record.title);

// 5. 选中 流程状态
if (record.status) {{
    await page.evaluate((targetStatus) => {{
        const el = document.querySelector('[data-field-id="{FIELD_IDS['status']}"]');
        if (el) {{
            const pills = Array.from(el.querySelectorAll('li.b-select-option'));
            const matched = pills.find(p => p.innerText.trim() === targetStatus);
            if (matched) matched.click();
        }}
    }}, record.status);
    await page.waitForTimeout(300);
}}

// 6. 填充 对标参考链接
if (record.ref_link) {{
    await fillField("{FIELD_IDS['ref_link']}", record.ref_link);
}}

// 7. 填充 核心爆点/痛点
if (record.hook) {{
    await fillField("{FIELD_IDS['hook']}", record.hook);
}}

// 8. 填充 本地素材路径
if (record.path) {{
    await fillField("{FIELD_IDS['path']}", record.path);
}}

// 9. 填充 成片与文案清单
if (record.assets) {{
    await fillField("{FIELD_IDS['assets']}", record.assets);
}}

// 10. 勾选 分发平台
if (record.platforms && record.platforms.length > 0) {{
    await page.evaluate((targetPlatforms) => {{
        const el = document.querySelector('[data-field-id="{FIELD_IDS['platforms']}"]');
        if (el) {{
            const pills = Array.from(el.querySelectorAll('li.b-select-option'));
            pills.forEach(p => {{
                if (targetPlatforms.includes(p.innerText.trim())) {{
                    p.click();
                }}
            }});
        }}
    }}, record.platforms);
    await page.waitForTimeout(300);
}}

// 11. 填充 全网播放数据
if (record.views !== undefined) {{
    const numSel = '#number-editor-input-{FIELD_IDS['views']}';
    const exists = await page.evaluate((sel) => !!document.querySelector(sel), numSel);
    if (exists) {{
        await page.fill(numSel, String(record.views));
        await page.waitForTimeout(200);
    }}
}}

// 12. 点击「提交」
console.log("Submitting record...");
await page.evaluate(() => {{
    const card = document.querySelector('.bitable-card-modal-v2');
    if (card) {{
        const btn = Array.from(card.querySelectorAll('button')).find(b => b.innerText.trim() === '提交');
        if (btn) btn.click();
    }}
}});
await page.waitForTimeout(2500);

// 关闭抽屉
await page.evaluate(() => {{
    const closeBtn = document.querySelector('.bitable-card-modal-header-v2-btn-close');
    if (closeBtn) closeBtn.click();
}});
await page.waitForTimeout(1000);
console.log("SUCCESS_SYNC_RECORD");
"""

    # 调用 ego-browser 运行该嵌入脚本
    proc = subprocess.run(
        ["ego-browser", "nodejs"],
        input=node_script,
        text=True,
        capture_output=True
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0 and "SUCCESS_SYNC_RECORD" in output:
        return True
    else:
        print(f"[-] 同步失败: {output}")
        return False


def main():
    parser = argparse.ArgumentParser(description="飞书多维表格自动化同步工具")
    parser.add_argument("target", nargs="?", default=".", help="待同步的选题工程目录路径（默认当前目录）")
    parser.add_argument("--scan", action="store_true", help="扫描目标目录下所有子工程批量同步")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()

    if args.scan:
        print(f"[*] 开始扫描目录: {target_path}")
        subdirs = sorted([d for d in target_path.iterdir() if d.is_dir()])
        records_to_sync = []
        for d in subdirs:
            rec = parse_project_dir(d)
            if rec:
                records_to_sync.append(rec)
        
        print(f"[+] 识别出 {len(records_to_sync)} 个有效自媒体工程:")
        for r in records_to_sync:
            print(f"  - [{r['status']}] {r['title']} ({Path(r['path']).name})")
        
        print("\n[*] 开始批量同步至飞书多维表格...")
        success_count = 0
        for r in records_to_sync:
            print(f" -> 正在推送: {r['title']} ...")
            if sync_record_via_browser(r):
                print(f"    [OK] 成功")
                success_count += 1
            else:
                print(f"    [FAIL] 失败")
        print(f"\n[√] 批量同步完成: 成功 {success_count} / {len(records_to_sync)}")

    else:
        rec = parse_project_dir(target_path)
        if not rec:
            print(f"[-] 目录 {target_path} 未识别到有效的脚本或视频产物。")
            sys.exit(1)

        print(f"[*] 解析到自媒体工程信息:")
        print(f"  - 选题标题:   {rec['title']}")
        print(f"  - 流程状态:   {rec['status']}")
        print(f"  - 核心痛点:   {rec['hook']}")
        print(f"  - 交付清单:   {rec['assets']}")
        print(f"  - 素材路径:   {rec['path']}")
        print(f"  - 分发平台:   {', '.join(rec['platforms'])}")
        print(f"\n[*] 正在同步至飞书...")

        if sync_record_via_browser(rec):
            print(f"[√] 成功同步至飞书「AI自媒体自动化·选题与出片总表」！")
        else:
            print(f"[-] 同步失败，请检查浏览器会话状态。")


if __name__ == "__main__":
    main()
