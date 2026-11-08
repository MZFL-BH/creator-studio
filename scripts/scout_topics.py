#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creator Studio · 选题雷达与 85 分团队打分引擎 (Topic Scout & Scorer)
=====================================================================
复刻 Grok Bot 团队评审机制，专为 Ethan 硬核技术实测赛道量身定制：
1. [多源情报抓取] 自动拉取 GitHub AI Trending、Hacker News AI 争议热榜、Hugging Face 每日最新突破；
2. [单选题手动裁决] 支持手动输入任意竞品链接或选题痛点进行 85 分打分；
3. [五维团队打分机制]：
   - 痛点与反常识冲突 (25分)
   - 真实实测可行性 (20分)
   - 利他价值与赞藏比潜力 (20分)
   - 长尾搜索与公域爆发力 (20分)
   - 极客信誉与开源转化 (15分)
4. [硬核门槛拦截] 仅当综合得分 >= 85 分时才准予立项，自动输出核心冲突点与实测方案；
5. [一键咬合流水线] 支持 --init 自动初始化工程目录 (generate_script.py)，支持 --sync-feishu 入库飞书。
"""

import os
import sys
import json
import re
import argparse
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

SKILL_ROOT = Path("/Users/wangbinghao/.gemini/config/skills")
GENERATE_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "generate_script.py"
FEISHU_SYNC_SCRIPT = SKILL_ROOT / "creator-studio" / "scripts" / "feishu_sync.py"
DESKTOP_DIR = Path.home() / "Desktop" / "素材"


# --- 1. 多源情报数据源抓取 ---

def fetch_github_trending(limit=6):
    """通过 GitHub CLI 或 API 抓取高热度 AI 开源项目"""
    print("[*] 正在扫描 GitHub AI 热门开源项目...")
    items = []
    try:
        cmd = ["gh", "api", "search/repositories?q=AI+topic:ai&sort=stars&order=desc&per_page=10", "--jq", ".items[] | {name: .full_name, stars: .stargazers_count, desc: .description, url: .html_url}"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        repo = json.loads(line)
                        items.append({
                            "source": "GitHub Trending",
                            "title": repo.get("name"),
                            "summary": repo.get("desc") or "无描述",
                            "url": repo.get("url"),
                            "metric": f"{repo.get('stars', 0):,} Stars"
                        })
                    except Exception:
                        pass
    except Exception as e:
        print(f"[-] GitHub 抓取略过: {e}")
    return items[:limit]


def fetch_hacker_news_ai(limit=6):
    """抓取 Hacker News 硅谷极客圈 AI 争议与讨论焦点"""
    print("[*] 正在扫描 Hacker News AI 极客争议榜...")
    items = []
    try:
        url = "https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=10"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            for h in data.get("hits", [])[:limit]:
                items.append({
                    "source": "Hacker News",
                    "title": h.get("title"),
                    "summary": f"社区点赞 {h.get('points')}，评论讨论 {h.get('num_comments')} 条",
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "metric": f"{h.get('points', 0)} pts"
                })
    except Exception as e:
        print(f"[-] Hacker News 抓取略过: {e}")
    return items[:limit]


def fetch_huggingface_papers(limit=6):
    """抓取 Hugging Face 每日最新突破与模型边界"""
    print("[*] 正在扫描 Hugging Face 每日研究与突破...")
    items = []
    try:
        url = "https://huggingface.co/api/daily_papers"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            for p in data[:limit]:
                paper = p.get("paper", {})
                items.append({
                    "source": "Hugging Face",
                    "title": paper.get("title") or p.get("title"),
                    "summary": paper.get("summary", "")[:120] + "...",
                    "url": f"https://huggingface.co/papers/{p.get('id')}",
                    "metric": "Daily Paper"
                })
    except Exception as e:
        print(f"[-] Hugging Face 抓取略过: {e}")
    return items[:limit]


# --- 2. 团队化 85 分打分模型算法 ---

def score_topic(title: str, summary: str = "", source: str = "手动输入") -> dict:
    """
    五维团队打分模型 (总分 100 分，85 分准入门槛线)：
    1. 痛点与反常识冲突 (Conflict, 25分)
    2. 真实实测可行性 (Feasibility, 20分)
    3. 利他价值与赞藏比潜力 (Utility, 20分)
    4. 长尾搜索与公域爆发力 (Search, 20分)
    5. 极客信誉与开源转化 (Authority, 15分)
    """
    text = (title + " " + summary).lower()

    # 1. 痛点与反常识冲突 (0~25)
    # 高反差词：造假、翻车、做不到、闭坑、真相、私自、糊弄、虚假、真实、为什么不
    conflict_score = 15
    if any(k in text for k in ["翻车", "造假", "做不到", "避坑", "真相", "背刺", "私自", "糊弄", "忽悠", "fake", "flaw", "bench", "vs", "vs.", "compare"]):
        conflict_score += 9
    elif any(k in text for k in ["实测", "测评", "对比", "评价", "坑", "测试", "真实", "问题", "bug", "issue"]):
        conflict_score += 6
    conflict_score = min(25, max(10, conflict_score))

    # 2. 真实实测可行性 (0~20)
    # 能在本地跑代码、跑终端、用大模型跑任务
    feasibility_score = 13
    if any(k in text for k in ["ppt", "周报", "简历", "agent", "python", "代码", "自动化", "模型", "提示词", "workflow", "script", "tool", "cli"]):
        feasibility_score += 6
    elif any(k in text for k in ["开源", "框架", "api", "本地", "测试", "demo", "repo"]):
        feasibility_score += 4
    feasibility_score = min(20, max(8, feasibility_score))

    # 3. 利他价值与赞藏比潜力 (0~20)
    # 观众能不能拿走东西：清单、模板、原件、脚本
    utility_score = 12
    if any(k in text for k in ["模板", "原件", "清单", "sop", "技巧", "脚本", "方法", "核对", "避坑", "教程", "guide", "cheatsheet", "template"]):
        utility_score += 7
    elif any(k in text for k in ["省时间", "提效", "效率", "经验", "干货"]):
        utility_score += 5
    utility_score = min(20, max(8, utility_score))

    # 4. 长尾搜索与公域爆发力 (0~20)
    # 高频职场刚需或头部AI热词：DeepSeek, WPS, Grok, GPT, 微信, 汇报, 职场, 面试
    search_score = 13
    if any(k in text for k in ["deepseek", "grok", "wps", "gemini", "chatgpt", "claude", "豆包", "ppt", "周报", "面试", "求职", "自媒体"]):
        search_score += 6
    elif any(k in text for k in ["ai", "大模型", "智能体", "agent", "工作", "效率"]):
        search_score += 4
    search_score = min(20, max(8, search_score))

    # 5. 极客信誉与开源转化 (0~15)
    # 能否沉淀 GitHub Star、自研工具链传播
    authority_score = 10
    if any(k in text for k in ["github", "开源", "star", "代码", "自研", "python", "pipeline", "framework"]):
        authority_score += 5
    elif any(k in text for k in ["硬核", "工程", "实操", "技术", "架构"]):
        authority_score += 3
    authority_score = min(15, max(6, authority_score))

    total = conflict_score + feasibility_score + utility_score + search_score + authority_score
    passed = total >= 85

    # 自动提炼核心 Hook 与实测切入点
    hook_proposal = f"网上一堆人吹 {title} / 今天拿真实业务死磕实测 / 结果发现表面高大上，背地里全是坑！"
    test_plan = f"在本地构建严格测试集，横向对比 3~4 款主流工具表现，重点核对数据篡改与边界盲区。"

    return {
        "title": title,
        "source": source,
        "summary": summary,
        "total_score": total,
        "passed": passed,
        "dimensions": {
            "conflict": conflict_score,
            "feasibility": feasibility_score,
            "utility": utility_score,
            "search": search_score,
            "authority": authority_score
        },
        "hook_proposal": hook_proposal,
        "test_plan": test_plan
    }


def print_score_card(result: dict, rank: int = 1):
    status_icon = "🟢 [准入立项 (S级)]" if result["passed"] else "🔴 [淘汰过滤]"
    if 75 <= result["total_score"] < 85:
        status_icon = "🟡 [储备观察 (A级)]"

    print("\n" + "=" * 64)
    print(f"选题 #{rank}：【{result['title']}】 {status_icon}")
    print(f"来源平台：{result['source']} | 综合得分：{result['total_score']} / 100 分 (门槛线: 85分)")
    print("-" * 64)
    dims = result["dimensions"]
    print(f"• 痛点与反常识冲突: {dims['conflict']}/25 分")
    print(f"• 真实实测可行性:   {dims['feasibility']}/20 分")
    print(f"• 利他价值与赞藏比: {dims['utility']}/20 分")
    print(f"• 长尾搜索爆发力:   {dims['search']}/20 分")
    print(f"• 极客信誉与转化:   {dims['authority']}/15 分")
    print("-" * 64)
    print(f"💡 黄金 3 秒 Hook 预设: {result['hook_proposal']}")
    print(f"🔬 建议实测落地方案:    {result['test_plan']}")
    print("=" * 64)


# --- 3. 主入口逻辑 ---

def main():
    parser = argparse.ArgumentParser(description="Creator Studio · 选题雷达与 85 分打分引擎")
    parser.add_argument("topic", nargs="?", default="", help="手动评估的选题名称或竞品链接")
    parser.add_argument("--scan", action="store_true", help="自动并发扫描 GitHub、HackerNews、HuggingFace 全球 AI 情报")
    parser.add_argument("--limit", type=int, default=5, help="展示高潜选题数量")
    parser.add_argument("--min-score", type=int, default=85, help="准入门槛分数 (默认 85 分)")
    parser.add_argument("--init", action="store_true", help="为得分最高的准入选题直接调用 generate_script.py 初始化出片工程")
    parser.add_argument("--sync-feishu", action="store_true", help="将得分 >= 85 的选题自动录入飞书多维表格")
    args = parser.parse_args()

    candidates = []

    # 1. 手动输入单一选题打分
    if args.topic:
        candidates.append({"title": args.topic, "summary": "手动录入的候选实测主题", "source": "手工输入"})

    # 2. 扫描各大情报平台
    if args.scan or not args.topic:
        gh_items = fetch_github_trending(5)
        hn_items = fetch_hacker_news_ai(5)
        hf_items = fetch_huggingface_papers(5)
        candidates.extend(gh_items + hn_items + hf_items)

    if not candidates:
        print("[-] 未获取到任何有效选题情报。")
        return

    # 3. 运行 85 分团队评审打分模型
    results = []
    for c in candidates:
        res = score_topic(c.get("title", ""), c.get("summary", ""), c.get("source", "情报雷达"))
        results.append(res)

    # 按分数降序排列
    results.sort(key=lambda x: x["total_score"], reverse=True)

    # 4. 统计与呈现
    passed_items = [r for r in results if r["total_score"] >= args.min_score]
    print(f"\n🎯 选题评审完毕！共评估 {len(results)} 条候选，通过 85 分门槛线共 {len(passed_items)} 条。")

    top_display = results[:args.limit]
    for idx, r in enumerate(top_display, 1):
        print_score_card(r, idx)

    # 5. 若指定 --init，自动初始化最高分选题工程
    if args.init and passed_items:
        top_pass = passed_items[0]
        # 清洗目录名
        safe_name = re.sub(r'[^\w\-\u4e00-\u9fa5]', '_', top_pass['title'])[:24]
        date_str = datetime.now().strftime("%Y%m%d")
        proj_dir = DESKTOP_DIR / f"{date_str}-{safe_name}"
        
        print(f"\n🚀 自动立项并初始化工程: {proj_dir.name}")
        cmd = [sys.executable, str(GENERATE_SCRIPT), top_pass['title'], "-o", str(proj_dir), "-c", "选题雷达高潜对标", "-e", top_pass['test_plan']]
        subprocess.run(cmd)

    # 6. 若指定 --sync-feishu，将通过选题录入飞书
    if args.sync_feishu and passed_items:
        print("\n☁️ 正在将高潜选题同步至飞书多维表格「待出片总表」...")
        for r in passed_items:
            # 创建临时元数据结构同步
            temp_dir = DESKTOP_DIR / f"temp_{int(datetime.now().timestamp())}"
            temp_dir.mkdir(exist_ok=True)
            script_stub = temp_dir / "script.md"
            script_stub.write_text(f"# {r['title']}\n\n## 出镜 ① F01\n口播: {r['hook_proposal']}\n", encoding="utf-8")
            subprocess.run([sys.executable, str(FEISHU_SYNC_SCRIPT), str(temp_dir)])
            # 清理临时
            for f in temp_dir.iterdir():
                f.unlink()
            temp_dir.rmdir()
        print("[√] 飞书同步完成！")


if __name__ == "__main__":
    main()
