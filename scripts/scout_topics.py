#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creator Studio · 选题雷达与 85 分打分引擎 (Topic Scout & Rubric Scorer)
=====================================================================
融合 cheat-on-content 核心评估体系 (7 维度 Rubric + candidate-schema 协议)
与 6 年自媒体老兵经验，专为 Ethan 硬核技术实测赛道量身定制：

1. [7 维度团队打分模型] (满分 100 分，85 分为 S 级硬核准入门槛)：
   - ER (认知突破/顿悟感, ×1.5)
   - HP (黄金钩子/痛点狠话, ×1.5)
   - QL (可复制密度/抄作业, ×1.5)
   - NA (递进弧线/实测三幕, ×1.0)
   - AB (受众面普适度, ×1.0)
   - SR (技术风口共振, ×1.0)
   - SAT (真实人格感/撕滤镜, ×1.0)
   公式：composite = (ER×1.5 + HP×1.5 + QL×1.5 + NA + AB + SR + SAT) / 8.5 × 2.0
   换算：score_100 = round(composite * 10, 1)

2. [多源全球情报雷达]：
   - GitHub AI Trending (高赞开源项目、自研复现切入点)
   - Hacker News AI Hot (硅谷技术争议、开发者吐槽热帖)
   - Hugging Face Daily Papers (前沿模型突破、学术边界)

3. [候选池管理与协议对齐]：
   - 自动生成 12 位稳定 hash id：sha256(source:title:url)[:12]
   - 支持写入/读取 candidates.md，严格符合 candidate-schema.md 规范
   - 分级：tier1 (S级准入 ≥85分) / tier2 (A级储备 75-84分) / tier3 (淘汰 <75分)

4. [全流程一键贯通]：
   - --recommend: 从 candidates.md 检索并排序推荐高潜选题
   - --init: 选中高潜题目直接联动 generate_script.py 初始化分镜头工程
   - --sync-feishu: 准入选题无缝同步飞书多维表格「待出片总表」
"""

import os
import sys
import json
import re
import hashlib
import argparse
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

SKILL_ROOT = Path("/Users/wangbinghao/.gemini/config/skills")
GENERATE_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "generate_script.py"
FEISHU_SYNC_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "feishu_sync.py"
DESKTOP_DIR = Path.home() / "Desktop" / "素材"
REPO_DIR = Path.home() / "Desktop" / "creator-studio"
CANDIDATES_FILE = DESKTOP_DIR / "candidates.md"


# --- 1. 多源情报数据源抓取 ---

def fetch_github_trending(limit=6):
    """抓取高热度 AI 开源项目 (支持 gh cli 与 API fallback)"""
    print("[*] 正在扫描 GitHub AI 热门开源项目...")
    items = []
    # 优先尝试 gh cli
    try:
        cmd = [
            "gh", "api",
            "search/repositories?q=AI+topic:ai&sort=stars&order=desc&per_page=10",
            "--jq", ".items[] | {name: .full_name, stars: .stargazers_count, desc: .description, url: .html_url}"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        repo = json.loads(line)
                        items.append({
                            "source": "trend:github",
                            "title": repo.get("name"),
                            "summary": repo.get("desc") or "无描述",
                            "url": repo.get("url"),
                            "metric": f"{repo.get('stars', 0):,} Stars",
                            "category": "开源复现与评测"
                        })
                    except Exception:
                        pass
    except Exception:
        pass

    # 若未获取到则通过 HTTPS API fallback
    if not items:
        try:
            url = "https://api.github.com/search/repositories?q=AI+topic:ai&sort=stars&order=desc&per_page=10"
            req = urllib.request.Request(url, headers={"User-Agent": "CreatorStudio-Scout/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
                for repo in data.get("items", []):
                    items.append({
                        "source": "trend:github",
                        "title": repo.get("full_name"),
                        "summary": repo.get("description") or "无描述",
                        "url": repo.get("html_url"),
                        "metric": f"{repo.get('stargazers_count', 0):,} Stars",
                        "category": "开源复现与评测"
                    })
        except Exception as e:
            print(f"[-] GitHub 抓取略过: {e}")

    return items[:limit]


def fetch_hacker_news_ai(limit=6):
    """抓取 Hacker News 硅谷极客圈 AI 争议与热议焦点"""
    print("[*] 正在扫描 Hacker News AI 极客争议榜...")
    items = []
    try:
        url = "https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=10"
        req = urllib.request.Request(url, headers={"User-Agent": "CreatorStudio-Scout/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            for h in data.get("hits", [])[:limit]:
                items.append({
                    "source": "trend:hackernews",
                    "title": h.get("title"),
                    "summary": f"社区点赞 {h.get('points', 0)}，讨论 {h.get('num_comments', 0)} 条",
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "metric": f"{h.get('points', 0)} pts",
                    "category": "极客争议与反常识"
                })
    except Exception as e:
        print(f"[-] Hacker News 抓取略过: {e}")
    return items[:limit]


def fetch_huggingface_papers(limit=6):
    """抓取 Hugging Face 每日研究与突破"""
    print("[*] 正在扫描 Hugging Face 每日突破与前沿论文...")
    items = []
    try:
        url = "https://huggingface.co/api/daily_papers"
        req = urllib.request.Request(url, headers={"User-Agent": "CreatorStudio-Scout/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            for p in data[:limit]:
                paper = p.get("paper", {})
                items.append({
                    "source": "trend:huggingface",
                    "title": paper.get("title") or p.get("title"),
                    "summary": (paper.get("summary", "") or "")[:120] + "...",
                    "url": f"https://huggingface.co/papers/{p.get('id')}",
                    "metric": "Daily Paper",
                    "category": "模型技术突破"
                })
    except Exception as e:
        print(f"[-] Hugging Face 抓取略过: {e}")
    return items[:limit]


# --- 2. cheat-on-content 7 维度打分引擎 ---

def generate_candidate_id(source: str, title: str, url: str = "") -> str:
    """生成稳定 12 位 sha256 唯一指纹"""
    raw = f"{source}:{title.strip().lower()}:{url.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def score_topic(title: str, summary: str = "", source: str = "paste:manual", url: str = "", category: str = "AI工具实测") -> dict:
    """
    按 cheat-on-content 协议进行 7 维度 Rubric 打分：
    - ER (认知突破/顿悟感, 0-5, 权重 1.5)
    - HP (黄金钩子/痛点狠话, 0-5, 权重 1.5)
    - QL (可复制密度/抄作业, 0-5, 权重 1.5)
    - NA (递进弧线/实测三幕, 0-5, 权重 1.0)
    - AB (受众面普适度, 0-5, 权重 1.0)
    - SR (技术风口共振, 0-5, 权重 1.0)
    - SAT (真实人格感/撕滤镜, 0-5, 权重 1.0)

    准入门槛：composite >= 8.5 (即百分制 >= 85 分)
    """
    text = f"{title} {summary}".lower()

    # 1. ER: 认知突破 / 顿悟感 (0-5)
    # 核心：观众看完能否产生“原来他们都在吹牛/原来底层原理是这样”的恍然大悟
    er = 2
    if any(k in text for k in ["造假", "翻车", "做不到", "避坑", "真相", "背刺", "私自", "糊弄", "忽悠", "骗局", "fake", "flaw", "bench", "vs", "compare", "leak", "bug", "scam", "trap", "myth", "security"]):
        er += 2
    if any(k in text for k in ["实测", "测评", "对比", "评价", "分析", "benchmark", "eval", "test", "audit", "为什么不"]):
        er += 1
    er = min(5, max(1, er))

    # 2. HP: 黄金钩子 / 痛点狠话 (0-5)
    # 核心：前 3 秒能不能让观众立刻确认“这说的就是我工位上的痛”
    hp = 2
    if any(k in text for k in ["周报", "简历", "ppt", "面试", "求职", "裁员", "涨薪", "降本", "内卷", "自动化", "提效", "省时", "work", "job", "career", "productivity"]):
        hp += 2
    if any(k in text for k in ["千万别", "立刻停手", "为什么", "别再", "被忽悠", "浪费时间", "陷阱", "stop", "never", "why", "坑"]):
        hp += 1
    hp = min(5, max(1, hp))

    # 3. QL: 可复制密度 / 抄作业 (0-5)
    # 核心：视频包含多少可直接带走的交付物（代码、模板、原件、对比总表、SOP）
    ql = 2
    if any(k in text for k in ["模板", "原件", "清单", "sop", "技巧", "脚本", "代码", "框架", "prompt", "提示词", "workflow", "script", "cli", "template", "cheatsheet", "guide", "starter", "docker", "pipeline"]):
        ql += 2
    if any(k in text for k in ["开源", "配置", "教程", "步骤", "快速上手", "实操", "tutorial", "howto", "setup", "方法"]):
        ql += 1
    ql = min(5, max(1, ql))

    # 4. NA: 递进弧线 / 实测三幕 (0-5)
    # 核心：紧凑的三幕式结构：标准规则/官方吹捧 ➡️ 现场大翻车 ➡️ 终审自保解法
    has_conflict = any(k in text for k in ["翻车", "避坑", "真相", "vs", "对比", "bug", "坑", "issue"])
    has_solution = any(k in text for k in ["sop", "模板", "脚本", "解法", "实测", "方案", "guide"])
    if has_conflict and has_solution:
        na = 5
    elif has_conflict or has_solution:
        na = 4
    else:
        na = 3

    # 5. AB: 痛点普适度 / 受众面 (0-5)
    # 核心：周报、PPT、求职、效率自动化等千万级受众
    if any(k in text for k in ["周报", "ppt", "简历", "办公", "求职", "自媒体", "微信", "视频", "excel", "word", "pdf", "chatgpt", "deepseek", "wps"]):
        ab = 5
    elif any(k in text for k in ["python", "agent", "智能体", "大模型", "llm", "ai", "开源", "代码", "github", "自动化", "browser"]):
        ab = 4
    elif any(k in text for k in ["cuda", "kernel", "compiler", "quant", "rust", "c++", "paper", "dataset"]):
        ab = 3
    else:
        ab = 2

    # 6. SR: 技术风口共振 (0-5)
    # 核心：头部顶流工具或模型发布期（DeepSeek、Grok、WPS、Cursor、Agentic）
    if any(k in text for k in ["deepseek", "grok", "cursor", "gemini", "claude", "wps", "豆包", "openai", "qwen", "glm", "agentic", "reasoning", "r1"]):
        sr = 5
    elif any(k in text for k in ["ai", "大模型", "llm", "agent", "rag", "mcp", "transformer", "diffusion", "vision"]):
        sr = 4
    elif any(k in text for k in ["github", "docker", "linux", "cloud", "api"]):
        sr = 3
    else:
        sr = 2

    # 7. SAT: 真实人格感 / 撕滤镜 (0-5)
    # 核心：犀利直白、真实自嘲、对赛博糊弄的强烈愤怒，散发强极客魅力
    if any(k in text for k in ["实测", "真机", "自研", "手搓", "硬核", "工程", "翻车", "闭坑", "避坑", "亲自", "踩坑", "benchmark", "scratch"]):
        sat = 5
    elif any(k in text for k in ["评测", "测评", "对比", "分析", "代码", "开源"]):
        sat = 4
    else:
        sat = 3

    # 综合分计算
    weighted_sum = er * 1.5 + hp * 1.5 + ql * 1.5 + na * 1.0 + ab * 1.0 + sr * 1.0 + sat * 1.0
    composite = round((weighted_sum / 8.5) * 2.0, 2)
    total_score = round((composite / 10.0) * 100, 1)

    # 评级划分
    if total_score >= 85:
        tier = "tier1"
        passed = True
        predicted_bucket = "30-100w" if composite >= 9.2 else "10-50w"
    elif total_score >= 75:
        tier = "tier2"
        passed = False
        predicted_bucket = "5-30w"
    else:
        tier = "tier3"
        passed = False
        predicted_bucket = "<5w"

    cand_id = generate_candidate_id(source, title, url)

    # 黄金 3 秒钩子与实测落地方案
    hook = f"网上一堆人吹 {title} / 今天拿真实业务死磕真机实测 / 结果发现表面高大上，背地里全是坑！"
    test_plan = f"在本地搭建高严苛基准集，横向对比 3 款竞品，重点核查数据篡改与边界翻车率，交付开箱即用 SOP。"

    return {
        "id": cand_id,
        "title": title,
        "source": source,
        "url": url,
        "summary": summary,
        "category": category,
        "tier": tier,
        "passed": passed,
        "composite": composite,
        "total_score": total_score,
        "predicted_bucket": predicted_bucket,
        "dimensions": {
            "ER": er,
            "HP": hp,
            "QL": ql,
            "NA": na,
            "AB": ab,
            "SR": sr,
            "SAT": sat
        },
        "hook": hook,
        "test_plan": test_plan,
        "snapshot_at": datetime.now().strftime("%Y-%m-%d")
    }


def print_score_card(result: dict, rank: int = 1):
    tier_badges = {
        "tier1": "🟢 [S 级准入立项 (≥85分)]",
        "tier2": "🟡 [A 级储备观察 (75-84分)]",
        "tier3": "🔴 [淘汰过滤 (<75分)]"
    }
    badge = tier_badges.get(result["tier"], "⚪ [待定]")

    print("\n" + "=" * 68)
    print(f"选题 #{rank}：【{result['title']}】 {badge}")
    print(f"ID: {result['id']} | 来源: {result['source']} | 预测播放: {result['predicted_bucket']}")
    print(f"综合分: {result['composite']} (折算: {result['total_score']} / 100 分) | 准入门槛: 85 分")
    print("-" * 68)
    d = result["dimensions"]
    print(f"• ER (认知突破): {d['ER']}/5 (×1.5)   • HP (黄金钩子): {d['HP']}/5 (×1.5)   • QL (抄作业度): {d['QL']}/5 (×1.5)")
    print(f"• NA (递进弧线): {d['NA']}/5 (×1.0)   • AB (受众广度): {d['AB']}/5 (×1.0)   • SR (风口共振): {d['SR']}/5 (×1.0)")
    print(f"• SAT (极客撕滤镜): {d['SAT']}/5 (×1.0)")
    print("-" * 68)
    print(f"💡 黄金 3 秒 Hook 预设: {result['hook']}")
    print(f"🔬 建议实测落地方案:    {result['test_plan']}")
    print("=" * 68)


# --- 3. candidates.md 存储与推荐系统 ---

def load_candidates_from_file(file_path: Path = CANDIDATES_FILE) -> list:
    """按 candidate-schema 解析 candidates.md"""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8")
    entries = []
    # 按 ### [tier] 分割
    pattern = re.compile(r'^###\s*\[(.*?)\]\s*(.*?)$', re.M)
    splits = list(pattern.finditer(content))
    for i, match in enumerate(splits):
        tier_tag = match.group(1).strip()
        title = match.group(2).strip()
        start = match.end()
        end = splits[i+1].start() if i + 1 < len(splits) else len(content)
        block = content[start:end]

        def get_field(field_name, default=""):
            m = re.search(rf'^[ \t]*-[ \t]*\*\*{re.escape(field_name)}\*\*:[ \t]*(.*?)$', block, re.M)
            return m.group(1).strip() if m else default

        cand_id = get_field("id", "")
        source = get_field("source", "unknown")
        snapshot_at = get_field("snapshot_at", "")
        category = get_field("category", "未分类")
        url = get_field("url", "")
        hook = get_field("hook", "")
        test_plan = get_field("test_plan", "")
        predicted_bucket = get_field("predicted bucket", "")
        note = get_field("note", "")

        # 解析 composite
        comp_match = re.search(r'^[ \t]*-[ \t]*\*\*composite[^\*]*\*\*:[ \t]*([\d\.]+)(?:[ \t]*\(([\d\.]+)分\))?', block, re.M)
        composite = float(comp_match.group(1)) if comp_match else 0.0
        total_score = float(comp_match.group(2)) if (comp_match and comp_match.group(2)) else composite * 10

        entries.append({
            "id": cand_id,
            "title": title,
            "tier": tier_tag,
            "source": source,
            "snapshot_at": snapshot_at,
            "category": category,
            "url": url,
            "composite": composite,
            "total_score": total_score,
            "predicted_bucket": predicted_bucket,
            "hook": hook,
            "test_plan": test_plan,
            "note": note
        })
    return entries


def save_candidates_to_file(candidates: list, file_path: Path = CANDIDATES_FILE):
    """将候选持久化合并写入 candidates.md，自动去重"""
    existing_entries = load_candidates_from_file(file_path)
    existing_ids = {e["id"] for e in existing_entries if e["id"]}

    new_saved = 0
    to_append = []
    for c in candidates:
        if c["id"] not in existing_ids:
            to_append.append(c)
            existing_ids.add(c["id"])
            new_saved += 1

    if not file_path.exists():
        header = (
            "# 选题候选池 (Candidates Pool)\n\n"
            "> 由 Creator Studio + cheat-on-content 自动化维护。\n"
            "> 准入规则：S 级 (≥85分，直接立项出片) | A 级 (75-84分，储备观察) | 淘汰 (<75分)\n\n"
            "---\n\n"
        )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(header, encoding="utf-8")

    with file_path.open("a", encoding="utf-8") as f:
        for c in to_append:
            d = c.get("dimensions", {})
            dim_str = f"ER={d.get('ER', 0)} HP={d.get('HP', 0)} QL={d.get('QL', 0)} NA={d.get('NA', 0)} AB={d.get('AB', 0)} SR={d.get('SR', 0)} SAT={d.get('SAT', 0)}"
            entry_md = (
                f"### [{c['tier']}] {c['title']}\n"
                f"- **id**: {c['id']}\n"
                f"- **source**: {c['source']}\n"
                f"- **snapshot_at**: {c['snapshot_at']}\n"
                f"- **category**: {c.get('category', 'AI工具实测')}\n"
                f"- **url**: {c.get('url', '')}\n"
                f"- **composite (v1)**: {c['composite']} ({c['total_score']}分) — {dim_str}\n"
                f"- **tier**: {c['tier']}\n"
                f"- **predicted bucket**: {c.get('predicted_bucket', '10-50w')}\n"
                f"- **hook**: {c.get('hook', '')}\n"
                f"- **test_plan**: {c.get('test_plan', '')}\n"
                f"- **note**: \n\n"
            )
            f.write(entry_md)

    if new_saved > 0:
        print(f"[√] 成功入库 {new_saved} 条新候选至 {file_path.name}")
    return new_saved


def recommend_topics(file_path: Path = CANDIDATES_FILE, top_n: int = 5, filter_tier: str = "tier1"):
    """从 candidates.md 中按 composite 排序推荐 top N 选题"""
    entries = load_candidates_from_file(file_path)
    if not entries:
        print(f"[-] 候选池目前为空或未找到: {file_path}")
        print("💡 建议方式：运行 `python3 scout_topics.py --scan --save` 自动从 GitHub/HN/HF 抓取并打分录入。")
        return

    # 过滤
    if filter_tier != "all":
        filtered = [e for e in entries if e["tier"] == filter_tier]
    else:
        filtered = entries

    if not filtered:
        print(f"[-] 在候选池中未找到符合 [{filter_tier}] 条件的选题。当前总储备: {len(entries)} 条。")
        return

    filtered.sort(key=lambda x: x["composite"], reverse=True)
    top_items = filtered[:top_n]

    print("\n" + "=" * 68)
    print(f"🎯 Creator Studio · 候选池智能推荐 (Top {len(top_items)}，筛选: {filter_tier})")
    print(f"数据源: {file_path} (池内总量: {len(entries)} 条)")
    print("=" * 68)

    for i, item in enumerate(top_items, 1):
        tier_flag = "🟢 S级准入" if item["tier"] == "tier1" else "🟡 A级储备"
        print(f"\n【推荐 #{i}】{item['title']}")
        print(f"• ID: {item['id']} | 分级: {tier_flag} | 综合得分: {item['total_score']}分 (composite: {item['composite']})")
        print(f"• 来源: {item['source']} | 预测播放: {item.get('predicted_bucket', '10-50w')} | 录入日期: {item['snapshot_at']}")
        if item.get("hook"):
            print(f"• 黄金钩子 Hook: {item['hook']}")
        if item.get("test_plan"):
            print(f"• 实测方案 SOP:   {item['test_plan']}")
        if item.get("url"):
            print(f"• 原始链接:      {item['url']}")
        print("-" * 68)


# --- 4. 主程序入口 ---

def main():
    parser = argparse.ArgumentParser(description="Creator Studio · 选题雷达与 cheat-on-content 85分评审引擎")
    parser.add_argument("topic", nargs="?", default="", help="手动评估的选题名称或竞品链接")
    parser.add_argument("--scan", action="store_true", help="并发抓取 GitHub、HackerNews、HuggingFace 全球 AI 情报")
    parser.add_argument("--limit", type=int, default=5, help="展示高潜选题数量 (默认 5)")
    parser.add_argument("--min-score", type=int, default=85, help="准入门槛分数 (默认 85 分)")
    parser.add_argument("--save", action="store_true", help="将扫描或打分的候选保存至 candidates.md")
    parser.add_argument("--recommend", action="store_true", help="从 candidates.md 排序推荐高潜选题")
    parser.add_argument("--filter", default="tier1", choices=["all", "tier1", "tier2"], help="推荐时的等级过滤 (默认 tier1)")
    parser.add_argument("--init", action="store_true", help="为得分最高的准入选题直接调用 generate_script.py 初始化出片工程")
    parser.add_argument("--sync-feishu", action="store_true", help="将得分 >= 85 的准入选题自动录入飞书多维表格")
    args = parser.parse_args()

    # 1. 模式一：纯推荐已有候选池
    if args.recommend:
        recommend_topics(CANDIDATES_FILE, top_n=args.limit, filter_tier=args.filter)
        return

    candidates = []

    # 2. 模式二：手动输入单一选题评测
    if args.topic:
        candidates.append({
            "title": args.topic,
            "summary": "手工录入的候选实测主题",
            "source": "paste:manual",
            "url": args.topic if args.topic.startswith("http") else "",
            "category": "自选实测"
        })

    # 3. 模式三：情报雷达全网扫描
    if args.scan or not args.topic:
        gh_items = fetch_github_trending(6)
        hn_items = fetch_hacker_news_ai(6)
        hf_items = fetch_huggingface_papers(6)
        candidates.extend(gh_items + hn_items + hf_items)

    if not candidates:
        print("[-] 未获取到任何有效选题情报。")
        return

    # 4. 运行 cheat-on-content 7 维打分
    results = []
    for c in candidates:
        res = score_topic(
            title=c.get("title", ""),
            summary=c.get("summary", ""),
            source=c.get("source", "trend:radar"),
            url=c.get("url", ""),
            category=c.get("category", "AI工具实测")
        )
        results.append(res)

    # 降序排序
    results.sort(key=lambda x: x["composite"], reverse=True)

    passed_items = [r for r in results if r["total_score"] >= args.min_score]
    print(f"\n🎯 选题评审完毕！共评估 {len(results)} 条候选，通过 85 分门槛线 (S级) 共 {len(passed_items)} 条。")

    top_display = results[:args.limit]
    for idx, r in enumerate(top_display, 1):
        print_score_card(r, idx)

    # 5. 持久化存储至 candidates.md (若指定 --save 或扫描时默认入库 S/A 级)
    if args.save or args.scan:
        # 只持久化 tier1 与 tier2 (>=75分) 的优质候选，保持池子高价值
        worthy_candidates = [r for r in results if r["tier"] in ["tier1", "tier2"]]
        if worthy_candidates:
            save_candidates_to_file(worthy_candidates, CANDIDATES_FILE)
            # 同步更新 repo 根目录
            if REPO_DIR.exists():
                save_candidates_to_file(worthy_candidates, REPO_DIR / "candidates.md")

    # 6. 若指定 --init，自动为第 1 名准入选题初始化工程
    if args.init and passed_items:
        top_pass = passed_items[0]
        safe_name = re.sub(r'[^\w\-\u4e00-\u9fa5]', '_', top_pass['title'])[:24]
        date_str = datetime.now().strftime("%Y%m%d")
        proj_dir = DESKTOP_DIR / f"{date_str}-{safe_name}"

        print(f"\n🚀 自动立项并初始化分镜头工程: {proj_dir.name}")
        cmd = [sys.executable, str(GENERATE_SCRIPT), top_pass['title'], "-o", str(proj_dir), "-c", "选题雷达准入", "-e", top_pass['test_plan']]
        subprocess.run(cmd)

    # 7. 若指定 --sync-feishu，同步至飞书
    if args.sync_feishu and passed_items:
        print("\n☁️ 正在将准入选题同步至飞书多维表格「待出片总表」...")
        for r in passed_items:
            temp_dir = DESKTOP_DIR / f"temp_{int(datetime.now().timestamp())}"
            temp_dir.mkdir(exist_ok=True)
            script_stub = temp_dir / "script.md"
            script_stub.write_text(f"# {r['title']}\n\n## 出镜 ① F01\n口播: {r['hook']}\n", encoding="utf-8")
            subprocess.run([sys.executable, str(FEISHU_SYNC_SCRIPT), str(temp_dir)])
            for f in temp_dir.iterdir():
                f.unlink()
            temp_dir.rmdir()
        print("[√] 飞书同步完成！")


if __name__ == "__main__":
    main()
