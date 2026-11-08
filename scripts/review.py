#!/usr/bin/env python3
"""
Creator Studio · 视频作品复盘与数据体检脚本 (review.py)

功能：
1. 自动定位工程目录，读取分镜脚本 (script.md) 与发布文案 (publish.md) 的元数据与制作耗时；
2. 输入/读取平台核心量化指标（播放、2s跳出、5s完播、完播率、点赞、收藏、评论、转粉、GitHub Star）；
3. 严格按照老自媒体人四维健康线进行红黄绿诊断，标注 🔴 P0 / 🟠 P1 / 🟡 P2 级别；
4. 输出具象可落地的下一期 SOP 反哺建议，并在工程目录下生成《复盘体检报告》(review.md)；
5. 可选同步数据至飞书多维表格「全网播放数据」列。
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# 老博主四维健康标准线
HEALTH_BENCHMARKS = {
    "bounce_2s": {"label": "前 2 秒跳出率", "good": 0.40, "excellent": 0.25, "is_lower_better": True, "unit": "%"},
    "retention_5s": {"label": "5 秒完播率", "good": 0.25, "excellent": 0.40, "is_lower_better": False, "unit": "%"},
    "avg_progress": {"label": "平均播放进度", "good": 0.35, "excellent": 0.50, "is_lower_better": False, "unit": "%"},
    "save_like_ratio": {"label": "收藏点赞比", "good": 0.30, "excellent": 0.60, "is_lower_better": False, "unit": "%"},
    "follow_rate": {"label": "转粉转化率", "good": 0.01, "excellent": 0.025, "is_lower_better": False, "unit": "%"},
    "interaction_rate": {"label": "总互动率", "good": 0.04, "excellent": 0.08, "is_lower_better": False, "unit": "%"},
}

def parse_args():
    parser = argparse.ArgumentParser(description="自媒体出片数据复盘与诊断工具")
    parser.add_argument("project_dir", nargs="?", default="", help="视频工程目录路径或目录名（如 20261030-template-ppt）")
    parser.add_argument("--views", type=int, help="播放量 / 曝光量")
    parser.add_argument("--bounce2s", type=float, help="前2秒跳出率百分比（例如 35 表示 35%%）")
    parser.add_argument("--retention5s", type=float, help="5秒完播率百分比（例如 28 表示 28%%）")
    parser.add_argument("--progress", type=float, help="平均播放进度百分比（例如 42 表示 42%%）")
    parser.add_argument("--likes", type=int, help="点赞数")
    parser.add_argument("--saves", type=int, help="收藏数")
    parser.add_argument("--comments", type=int, help="评论数")
    parser.add_argument("--shares", type=int, help="转发/分享数")
    parser.add_argument("--follows", type=int, help="净增粉丝数")
    parser.add_argument("--stars", type=int, help="GitHub Star 新增数（若为开源选题）")
    parser.add_argument("--notes", type=str, default="", help="人工观察记录与观众典型反馈")
    parser.add_argument("--sync-feishu", action="store_true", help="是否尝试回填飞书多维表格")
    return parser.parse_args()

def locate_project(project_arg):
    base_dir = Path.home() / "Desktop" / "素材"
    if project_arg:
        p = Path(project_arg).expanduser()
        if p.is_dir():
            return p.resolve()
        candidate = base_dir / project_arg
        if candidate.is_dir():
            return candidate.resolve()
    
    # 未传参时，自动扫描最新修改的工程目录
    subdirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not subdirs:
        print(f"❌ 未在 {base_dir} 找到任何视频工程目录。")
        sys.exit(1)
    subdirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return subdirs[0].resolve()

def analyze_project_meta(project_path: Path):
    meta = {
        "title": project_path.name,
        "script_path": None,
        "publish_path": None,
        "has_loudnorm": False,
        "has_cover": False,
        "created_at": None,
        "estimated_duration_s": 0,
        "category": "60%~70% 硬核实测",
    }
    
    script_candidates = ["script.md", "full-script.md"]
    for s in script_candidates:
        sp = project_path / s
        if sp.exists():
            meta["script_path"] = sp
            try:
                content = sp.read_text(encoding="utf-8")
                # 粗略判断类型
                if "快讯" in content or "热点" in content or "首发" in content:
                    meta["category"] = "20%~30% 爆发快讯"
                elif "开源" in content or "Star" in content or "pipeline" in content:
                    meta["category"] = "隐形杀手锏·自研开源"
            except Exception:
                pass
            break
            
    pub_file = project_path / "publish.md"
    if pub_file.exists():
        meta["publish_path"] = pub_file

    loudnorm_files = list(project_path.glob("*_loudnorm.mp4"))
    meta["has_loudnorm"] = len(loudnorm_files) > 0

    cover_dirs = list(project_path.glob("*.oil-cover")) + list(project_path.glob("*cover*"))
    meta["has_cover"] = len(cover_dirs) > 0

    return meta

def prompt_metric(prompt_text, default_val=None, cast_type=int):
    if default_val is not None:
        p = f"{prompt_text} (回车默认 {default_val}): "
    else:
        p = f"{prompt_text}: "
    
    val_str = input(p).strip()
    if not val_str:
        return default_val
    try:
        return cast_type(val_str)
    except ValueError:
        print(f"⚠️ 输入格式有误，按默认值 {default_val} 计算。")
        return default_val

def collect_metrics_interactive(args, meta):
    print("\n" + "="*56)
    print(f"📊 开始进行作品复盘体检: 【{meta['title']}】")
    print("="*56)
    
    views = args.views if args.views is not None else prompt_metric("1. 视频总播放量 (Views)", 1000, int)
    views = max(1, views or 1)
    
    bounce2s = args.bounce2s if args.bounce2s is not None else prompt_metric("2. 前2秒跳出率 % (例如 38 表示 38%)", 35.0, float)
    retention5s = args.retention5s if args.retention5s is not None else prompt_metric("3. 5秒完播率 % (例如 28 表示 28%)", 28.0, float)
    progress = args.progress if args.progress is not None else prompt_metric("4. 平均播放进度 % (例如 38 表示 38%)", 36.0, float)
    likes = args.likes if args.likes is not None else prompt_metric("5. 点赞数", 45, int)
    saves = args.saves if args.saves is not None else prompt_metric("6. 收藏数 (技术视频生命线)", 30, int)
    comments = args.comments if args.comments is not None else prompt_metric("7. 评论数", 12, int)
    shares = args.shares if args.shares is not None else prompt_metric("8. 转发/分享数", 8, int)
    follows = args.follows if args.follows is not None else prompt_metric("9. 本条带来的净增关注数", 15, int)
    stars = args.stars if args.stars is not None else prompt_metric("10. GitHub 仓库 Star 新增数 (无则填 0)", 0, int)
    notes = args.notes if args.notes else input("11. 人工观察感悟 / 评论区最高频吐槽 (选填): ").strip()

    return {
        "views": views,
        "bounce2s": bounce2s,
        "retention5s": retention5s,
        "progress": progress,
        "likes": likes,
        "saves": saves,
        "comments": comments,
        "shares": shares,
        "follows": follows,
        "stars": stars,
        "notes": notes,
    }

def diagnose(data):
    v = data["views"]
    likes = data["likes"]
    saves = data["saves"]
    comments = data["comments"]
    shares = data["shares"]
    follows = data["follows"]
    
    # 比例计算
    save_like_ratio = (saves / likes * 100) if likes > 0 else 0
    like_view_ratio = (likes / v * 100) if v > 0 else 0
    interaction_rate = ((likes + saves + comments + shares) / v * 100)
    follow_rate = (follows / v * 100)
    
    issues = []
    strengths = []
    
    # 0. 小眼睛点赞比 (小红书/抖音通用爆款指标: likes / views)
    if v >= 500 and like_view_ratio < 2.0:
        issues.append({
            "level": "🟠 P1 (小眼睛点赞比过低/内容共鸣不足)",
            "dim": "小眼睛点赞比 (赞播比)",
            "val": f"{like_view_ratio:.2f}%",
            "target": "> 3.0% (优秀 > 5.0%)",
            "desc": "千次播放仅收获极少点赞，说明内容平铺直叙，缺少让观众拍案叫绝的'情绪共鸣点'或'认知反差点'。",
            "action": "在台词中加入替受众吐槽的职场金句，且口播务必带'嘴角上扬微笑感'，强化自信与亲和力。"
        })
    elif like_view_ratio >= 4.0:
        strengths.append(f"小眼睛点赞比达 {like_view_ratio:.2f}%，观众认可度与情绪共鸣度极高。")
    
    # 1. 片头诊断 (前2秒跳出率)
    b2 = data["bounce2s"]
    if b2 > 45:
        issues.append({
            "level": "🔴 P0 (阻塞级/流量断崖)",
            "dim": "片头黄金钩子",
            "val": f"{b2:.1f}%",
            "target": "< 40% (优秀 < 25%)",
            "desc": "近半数观众在前2秒划走！说明封面预期与开门第一句话完全脱节，或者开门在做无效自我介绍。",
            "action": "下期片头严禁用'大家好我是'，首帧直接甩出翻车大字卡或最具争议结论，剪辑前移 0.8 秒气口。"
        })
    elif b2 > 38:
        issues.append({
            "level": "🟡 P2 (业务增长瓶颈)",
            "dim": "片头黄金钩子",
            "val": f"{b2:.1f}%",
            "target": "< 40%",
            "desc": "跳出率及格但不够抓人，开门冲击力中规中矩。",
            "action": "片头第 1 秒必须出现情绪动词或视觉反差物料。"
        })
    else:
        strengths.append(f"前2秒跳出率低至 {b2:.1f}%，开门钩子极强，准确锁定了目标观众。")

    # 2. 5秒完播率
    r5 = data["retention5s"]
    if r5 < 20:
        issues.append({
            "level": "🔴 P0 (核心留存断层)",
            "dim": "5秒完播率",
            "val": f"{r5:.1f}%",
            "target": "> 25% (优秀 > 40%)",
            "desc": "观众在前5秒没有看到'我为什么必须看完'的理由，未能被算法推入次级流量池。",
            "action": "第 3~5 秒必须给出明确的利益点清单（'今天直接给你测4家，告诉你哪家能用哪家直接开除'）。"
        })
    elif r5 < 26:
        issues.append({
            "level": "🟠 P1 (严重级留存瓶颈)",
            "dim": "5秒完播率",
            "val": f"{r5:.1f}%",
            "target": "> 25%",
            "desc": "留存处于及格线边缘，前段节奏略有拖沓。",
            "action": "压缩前奏铺垫，5秒内完成'抛问题 -> 给承诺'闭环。"
        })
    else:
        strengths.append(f"5秒完播率达 {r5:.1f}%，成功把观众带入正题。")

    # 3. 收藏点赞比（技术视频核心护城河）
    if likes > 0 and save_like_ratio < 25:
        issues.append({
            "level": "🟠 P1 (内容硬核度与实用性断层)",
            "dim": "收藏点赞比",
            "val": f"{save_like_ratio:.1f}%",
            "target": "> 30% (优秀 > 60%)",
            "desc": "点赞虽有但收藏偏低，说明观众觉得'挺有趣'但'没用/不能抄作业'，无法激发工具书心理。",
            "action": "增加可直接复用的物料（如提示词模板、对比总表卡片、配置文件代码块），并在口播明确提示'建议收藏备用'。"
        })
    elif save_like_ratio >= 40:
        strengths.append(f"收藏点赞比高达 {save_like_ratio:.1f}%，具备极高的'抄作业'工具书属性，长尾搜索推荐潜力巨大。")

    # 4. 转粉率
    if follow_rate < 0.6:
        issues.append({
            "level": "🟡 P2 (人设转化沉淀偏弱)",
            "dim": "转粉转化率",
            "val": f"{follow_rate:.2f}%",
            "target": "> 1.0% (优秀 > 2.5%)",
            "desc": "大家看完了视频，但没有关注博主本人。人设定位存在感偏弱，沦为了内容工具人。",
            "action": "强化'Ethan 专撕 AI 营销'差异化标签，并在片尾抛出连载预期（如'下期我们直接开源这套脚本'）。"
        })
    elif follow_rate >= 1.2:
        strengths.append(f"转粉率达到 {follow_rate:.2f}%，人设吸引力强，有效将单期流量沉淀为长期资产。")

    return {
        "save_like_ratio": save_like_ratio,
        "like_view_ratio": like_view_ratio,
        "interaction_rate": interaction_rate,
        "follow_rate": follow_rate,
        "issues": issues,
        "strengths": strengths,
    }

def generate_report(project_path: Path, meta, data, diag):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_file = project_path / "review.md"

    # 生成 Markdown 报告
    lines = []
    lines.append(f"# 《自媒体作品复盘体检报告 · {meta['title']}》\n")
    lines.append(f"- **复盘时间**：{now_str}")
    lines.append(f"- **作品定位**：`{meta['category']}`")
    lines.append(f"- **制作物料**：分镜脚本 {'✅ 已归档' if meta['script_path'] else '⚠️ 缺失'} | 响度对齐 {'✅ 已执行' if meta['has_loudnorm'] else '⚠️ 未检测到'} | 封面计划 {'✅ 已生成' if meta['has_cover'] else '⚠️ 未生成'}")
    lines.append("\n---\n")

    lines.append("## 一、 核心量化指标看板\n")
    lines.append("| 诊断指标 | 实测数值 | 老博主及格线 | 优秀爆发线 | 状态判定 |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    def status_icon(val, target, is_lower=False):
        if is_lower:
            return "🟢 达标" if val <= target else "🔴 超标"
        return "🟢 达标" if val >= target else "🟠 待提升"

    lines.append(f"| **总播放量** | {data['views']:,} | - | - | 基础曝光池 |")
    lines.append(f"| **小眼睛点赞比** | {diag['like_view_ratio']:.2f}% | > 3.00% | > 5.00% | {status_icon(diag['like_view_ratio'], 3.0)} |")
    lines.append(f"| **前2秒跳出率** | {data['bounce2s']:.1f}% | < 40.0% | < 25.0% | {status_icon(data['bounce2s'], 40.0, True)} |")
    lines.append(f"| **5秒完播率** | {data['retention5s']:.1f}% | > 25.0% | > 40.0% | {status_icon(data['retention5s'], 25.0)} |")
    lines.append(f"| **平均播放进度** | {data['progress']:.1f}% | > 35.0% | > 50.0% | {status_icon(data['progress'], 35.0)} |")
    lines.append(f"| **收藏点赞比** | {diag['save_like_ratio']:.1f}% | > 30.0% | > 60.0% | {status_icon(diag['save_like_ratio'], 30.0)} |")
    lines.append(f"| **转粉转化率** | {diag['follow_rate']:.2f}% | > 1.00% | > 2.50% | {status_icon(diag['follow_rate'], 1.0)} |")
    lines.append(f"| **全网总互动率** | {diag['interaction_rate']:.2f}% | > 4.00% | > 8.00% | {status_icon(diag['interaction_rate'], 4.0)} |")
    if data['stars'] > 0:
        lines.append(f"| **GitHub Star 新增** | +{data['stars']} Stars | > 5 | > 30 | 🚀 开源转化闭环 |")
    lines.append("\n---\n")

    lines.append("## 二、 深度穿透体检结果 (P0 / P1 / P2 问题清单)\n")
    if not diag["issues"]:
        lines.append("🎉 **全项达标！** 本期视频各项数据表现均衡，可以直接将脚本模板固化为标准 SOP 范式。\n")
    else:
        for idx, item in enumerate(diag["issues"], 1):
            lines.append(f"### {idx}. 【{item['dim']}】{item['level']}")
            lines.append(f"- **现状指标**：`{item['val']}`（参考基准：`{item['target']}`）")
            lines.append(f"- **归因穿透**：{item['desc']}")
            lines.append(f"- **针对动作**：{item['action']}\n")

    lines.append("---\n")
    lines.append("## 三、 本期亮点与可复用资产\n")
    if diag["strengths"]:
        for s in diag["strengths"]:
            lines.append(f"- ✅ {s}")
    else:
        lines.append("- 本期完成了一整套全流程走通，验证了自动化管线的基础跑通。")
    if data["notes"]:
        lines.append(f"- 💡 **人工观察**：{data['notes']}")
    lines.append("\n---\n")

    lines.append("## 四、 下周工作日迭代建议 (SOP 反哺)\n")
    lines.append("结合你目前「周中抽出 2~3 晚各 1 小时打磨脚本，周末 3~4 小时集中出片」的节奏，下一期需做如下动作：")
    lines.append("1. **周中选题打磨期**：根据上方最高优先级的诊断问题（P0/P1），在 `script.md` 的前 3 秒钩子处实施针对性重构；")
    lines.append("2. **周末录剪期**：执行 `pipeline.py` 时保持音频 -14 LUFS 严格压制，若点赞收藏比欠佳，则增加 2 张以上对比卡片；")
    lines.append("3. **转化闭环期**：评论区首条必须置顶带引导的物料获取口令，承接高净值技术粉丝与 GitHub 仓库 Star。")

    report_content = "\n".join(lines)
    report_file.write_text(report_content, encoding="utf-8")
    return report_file, report_content

def main():
    args = parse_args()
    proj_dir = locate_project(args.project_dir)
    meta = analyze_project_meta(proj_dir)
    data = collect_metrics_interactive(args, meta)
    diag = diagnose(data)
    report_file, content = generate_report(proj_dir, meta, data, diag)

    print("\n" + "="*56)
    print(f"✅ 复盘诊断完成！已生成报告至:")
    print(f"👉 {report_file}")
    print("="*56)
    
    # 简要输出到控制台
    print("\n【核心诊断速览】")
    if diag["issues"]:
        for item in diag["issues"]:
            print(f"- {item['level']} | {item['dim']} (当前 {item['val']}) ➡️ {item['action']}")
    else:
        print("🌟 数据全线达标，节奏与转化极为健康！")
    print()

if __name__ == "__main__":
    main()
