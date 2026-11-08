#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creator Studio · 10分钟爆款脚本生成与抗压蒸馏引擎 (Generate Script)
===================================================================
深度吸收 6 年老自媒体博主（前大厂运营/MCN创始人）实操体系：
1. [三大黄金选题方向] AI工具硬核实测 (benchmark) / AI帮打工人省时间 (timesaver) / 用AI加速老赛道 (accelerator)。
2. [口播与台词铁律] 前3秒给狠话 + 把镜头当工位熟人 + 短句带【重音】+ 嘴角带笑录音法。
3. [网感剪辑双杠杆] 画中画证据叠加 + 3~5秒智能运镜跳切，杜绝单一口播大头娃娃。
4. [起步心法] 破除完美主义陷阱，60分流水线快速跑量，先开跑再优化。
5. [90天长效流量] 结构设计对齐中长横屏高完播率与高收藏率(>60%)。
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


SCRIPT_TEMPLATE = """# {title} · 3分钟硬核实测脚本 v1
> 口播台词用 `/` 分隔气口；`**加粗**` 为口播**重音强调**；【视觉】标注画中画与智能运镜；【状态】标注面部肌肉与语感。

## 出镜 ① F01 · 0:00–0:12 · 12s 【黄金3秒·前三秒给狠话】
Kicker overlay: {hook_kicker}
【口播台词】: {hook_voiceover}
【视觉画面】: 【中景切特写】Ethan 眼神锁定镜头，身体微前倾，右手拿手机或指向工位屏幕。
【状态语感】: 【嘴角微扬，自信坚定】把镜头当工位旁边的同事聊天，绝不用客套废话，开门第1秒直接扔出反常识狠话。

## C01 · RULE · 5s 【规则交代·拒绝玩具】
标题: 拒绝玩具Demo，**死磕真实生产力**
【视觉画面】: 【画中画全屏】展示真实业务场景（标准模板/内部规范/数据表），右下角保留口播小窗。
【口播台词】: {scene_voiceover}
【运镜动效】: 真实业务卡片从下向上滑入，核心规范参数红框高亮。

## C02 · DATA · 6s 【测试指标·原样死磕】
标题: {data_title}
【视觉画面】: 【画中画】核心测试指标胶囊标签依次点亮排列。
【口播台词】: {data_voiceover}
【运镜动效】: 数字标签自左向右依次亮起，末尾盖上「严格核实」红章。

## C03 · BENCHMARK · 5s 【竞品受阅·同台拉通】
标题: 顶流同台，**横向拉通横评**
【视觉画面】: 【全屏对比】多款主流工具/模型图标横向并排，底部出现对比标尺。
【口播台词】: {competitor_voiceover}
【运镜动效】: 各竞品图标依次落位，光效扫过。

## C04 · SCORECARD · 6s 【实测总表·戏剧冲突】
标题: {scorecard_title}
【视觉画面】: 【特写切客体】实测红绿勾叉总表横移进场，反差极其鲜明。
【口播台词】: {scorecard_voiceover}
【运镜动效】: 勾叉表自右向左平移，醒目红字放大提醒。

## C05 · TOOL1 · 6s 【实测一：坦承边界】
标题: {tool1_title}
【视觉画面】: 【画中画】截取工具回复首句高亮或核心对话界面。
【口播台词】: {tool1_voiceover}
【运镜动效】: 界面淡入，核心文字拉近特写。

## C06 · TOOL2 · 6s 【实测二：赛博糊弄】
标题: {tool2_title}
【视觉画面】: 【画中画】导出界面红圈标注翻车点或形式主义文字占位。
【口播台词】: {tool2_voiceover}
【运镜动效】: 翻车细节缩放跳动两次，音效「叮 / 金属警报」。

## 出镜 ② F02 · 1:15–1:27 · 12s 【二段钩子·揭秘深水区】
Kicker: DANGER
【口播台词】: {f02_voiceover}
【视觉画面】: 【近景特写】Ethan 神情由轻松转为严肃警示，身体微微前倾。
【状态语感】: 【神情收紧，语速从容下沉】重音加力，直接戳中观众对“背锅/翻车”的生存恐惧。

## C07 · ILLUSION · 6s 【数据陷阱·情绪共鸣】
标题: 表面风光，**背地里偷偷造假**
【视觉画面】: 【画中画全屏】4 张红框卡片横向并列，标题标「擅自脑补与私拆指标」。
【口播台词】: {illusion_voiceover}
【运镜动效】: 红框卡片如打桩机般逐一重重落下，警示感拉满。

## C08 · BOTTOM LINE · 5s 【职场生存金句】
标题: 排版丑挨顿批，**数据假要开除**
【视觉画面】: 【对比动效】天平两端对比：左边「视觉排版」轻 / 右边「真实责任」沉重下坠。
【口播台词】: 职场生存**第一定律** / 排版不好**挨顿骂** / 数据造假**背大锅**！
【运镜动效】: 天平迅速失衡，右侧数据重重砸到底部。

## C09 · SOP 1 · 5s 【解决方案·第1步】
标题: SOP ①：借**逻辑骨架**，不借填报
【视觉画面】: 【卡片动效】步骤 1 图标 + 结构树状图（结论→对比→风险→对策）。
【口播台词】: 正确姿势第一步 / 用它提炼**结论句**和**汇报骨架** / 绝不让它随意自由发挥！
【运镜动效】: 树状图节点依次生长点亮。

## C10 · SOP 2 · 5s 【解决方案·第2步】
标题: SOP ②：代码重构，**死磕精确还原**
【视觉画面】: 【画中画】步骤 2 图标 + 终端代码执行 / 自动化流水线。
【口播台词】: 真要批量套用 / 认准具备**代码生成与运行能力**的工具链！
【运镜动效】: 终端代码行刷刷滚过，输出高保真交付件。

## C11 · SOP 3 · 6s 【解决方案·第3步】
标题: SOP ③：建立**红线核对单**
【视觉画面】: 【画中画】步骤 3 图标 + 核对清单逐行打勾。
【口播台词】: 最关键一步 / 拿着原件逐行**核对关键指标** / 永远保留人类终审权！
【运镜动效】: 绿色勾号逐项打上，末尾盖章「人工终审通过」。

## C12 · KIT · 5s 【利他物料·拉高收藏率】
标题: 实测原件与避坑表**已整理**
【视觉画面】: 【画中画全览】完整资料包与对比清单同屏呈现，附下载箭头。
【口播台词】: {kit_voiceover}
【运镜动效】: 文件盒打开，比对表与实测清单滑出。

## 出镜 ③ F03 · 2:45–3:00 · 15s 【CTA 与 90 天长效收藏引导】
Kicker: CTA
【口播台词】: 我是 Ethan / 用 AI 解决**真实生产力问题**，公开实验 / 这期包含完整的对比清单与提示词，建议先【**收藏**】备查，避免后续踩坑找不到 / 评论区扣「{cta_keyword}」，原件直接打包带走！
【视觉画面】: 【中景切近景】Ethan 恢复【微笑亲和】，双手做抱拳或互动引导手势。
【状态语感】: 【嘴角上扬，真诚互动】给予观众极高确定感与利他价值，激活 >60% 高赞藏比。

## C13 · FOLLOW · 3s
标题: **Ethan** · 硬核技术实测
【视觉画面】: 关注卡片（头像 + 公开实验 / 真实职场）
【口播台词】: （片尾音效，字幕：关注不迷路）

---
## 本期拍摄与录屏物料清单 (Checklist)
1. 真人出镜 3 段 (F01 开头狠话、F02 中段警示、F03 结尾利他 CTA)
2. 真实业务场景 / 翻车证据录屏与截帧 (画中画素材)
3. 竞品实测勾叉总表
4. 整理好的打包资料包 (提示词 / 代码 / 对比表)
"""

PUBLISH_TEMPLATE = """# 《{title}》多平台分发文案库

---

## 一、 小红书 (RED / Xiaohongshu)
- **封面风格**: 3:4 竖版大字报，亮色黄底或红底粗黑体标题（如“千万别直接交！”“4款AI实测翻车实录”）。
- **笔记标题**: {xhs_title}
- **正文文案**:
{xhs_content}

- **标签 (Tags)**: #{topic_tag} #AI工具 #自媒体干货 #效率神器 #职场避坑 #干货分享
- **评论区置顶**:
> “完整实测对比原件 + 提示词核对单已打包整理完毕，需要的同学在评论区扣【{cta_keyword}】，看到都会分享！欢迎大家在评论区聊聊你们平时最常用的工具是什么~ 建议先【收藏】防走丢！”

---

## 二、 B站 (Bilibili)
- **封面风格**: 16:9 横版，高清实测大屏对比 + 人物严肃反差表情。
- **视频标题**: {bili_title}
- **简介文案**:
网上一堆教你用 AI 一键生成的教程，但真正放到真实工作场景，没人看花哨玩具，大家只要严谨可靠的交付结果！
今天我把真实业务模板和经营数据喂给 4 款顶流工具，死磕细节，带你看清：到底是谁在踏实干活，谁在赛博糊弄？

时间轴快捷跳转：
00:00 黄金开场：别再被花哨Demo忽悠了
00:45 规则公布：7个硬核指标原样写入
01:15 现场翻车：表面风光，背地里擅自加戏
02:10 避坑SOP：普通人如何用代码级工具自保？
02:45 资料获取与总结

- **互动引导**: 弹幕互动“你被哪家AI坑过？”；置顶评论附带 GitHub 开源地址或网盘链接。

---

## 三、 抖音 / 视频号 (Douyin / Channels)
- **形式机制**: 9:16 竖版高清 / 横屏中长视频（享受平台 90 天长效流量推荐扶持）。
- **视频文案**:
{douyin_content}
#{topic_tag} #自媒体创业 #AI玩家 #干货分享 #深度实测

- **评论区互动**: 引导在评论区留言【{cta_keyword}】触发自动私信或关键字回复。
"""


def generate_package(output_dir: Path, topic: str, topic_type: str, target: str, evidence: str, cta: str = "原件"):
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    title = f"{topic}横向深度测评" if "测评" not in topic else topic
    hook_kicker = "HOOK"

    # 根据三大黄金选题方向定制前3秒狠话
    if topic_type == "timesaver":
        hook_voiceover = f"网上一堆人教你用 AI 一键搞定 / 但真按他们的方法弄，**加班反而加更狠**！/ 今天教你一套自动化脚本 / 看看怎么把 3 小时活**压缩到 10 分钟**！"
        scorecard_title = "手动做累死人，**跑脚本秒交差**"
        scorecard_voiceover = f"实测对比非常夸张 / 手工一点点调格式要搞一晚上 / 跑通流水线只需点击运行！"
    elif topic_type == "accelerator":
        hook_voiceover = f"如果你还在用传统老办法做 {topic} / 我劝你**立刻停手**！/ 行业玩法已经彻底变了 / 今天用 AI 把这个老赛道重新跑一遍！"
        scorecard_title = "老办法寸步难行，**新工具降维打击**"
        scorecard_voiceover = f"实测下来极其颠覆 / 传统的重劳力环节 / 已经全部可以被 AI Agent 无缝接管！"
    else:  # benchmark
        hook_voiceover = f"如果你还在用网上教的 AI 做 {topic} / 我劝你**立刻停手**！/ 没人看花哨 Demo，大家只要**真实交付** / 今天把真实场景喂给顶流工具 / 结果测出一身冷汗：表面排版高大上，背地里居然**全员在偷偷造假**！"
        scorecard_title = "只有 1 个勉强合格，**0 个敢直接交**"
        scorecard_voiceover = f"实测结果非常戏剧性 / 真正能符合标准的寥寥无几 / **0 个敢不经审核直接交给领导**！"

    scene_voiceover = f"我准备了一套严格的真实业务测试集 / 包含了标准格式、严格规范和边界条件"
    data_title = "7 项核心指标**死磕原样**"
    data_voiceover = f"明确要求**原样输出**、**严禁私自篡改** / 看看在严格要求下，谁会原型毕露！"
    competitor_voiceover = f"同样的测试集和提示词 / 丢给行业主流工具和头部模型同台受阅"
    tool1_title = "头部工具 A：**坦承能力边界**"
    tool1_voiceover = f"第一位表现很诚实 / 明确告知当前环境的局限，不打诳语"
    tool2_title = "头部工具 B：**赛博形式主义**"
    tool2_voiceover = f"第二位看着热闹 / 导出一看全是用文字硬凑的假模版，纯属糊弄！"
    f02_voiceover = f"看到这你以为结束了？/ 真正让我冒冷汗的 / 是接下来深入核对核心细节时发现的**致命陷阱**！"
    illusion_voiceover = f"主流大模型 / 居然全部在**私自捏造数据和指标** / 没给的信息它也敢张口就来！"
    kit_voiceover = f"本次评测的完整提示词、测试集与翻车原件 / 我都已经整理打包完毕"

    script_content = SCRIPT_TEMPLATE.format(
        title=title,
        hook_kicker=hook_kicker,
        hook_voiceover=hook_voiceover,
        scene_voiceover=scene_voiceover,
        data_title=data_title,
        data_voiceover=data_voiceover,
        competitor_voiceover=competitor_voiceover,
        scorecard_title=scorecard_title,
        scorecard_voiceover=scorecard_voiceover,
        tool1_title=tool1_title,
        tool1_voiceover=tool1_voiceover,
        tool2_title=tool2_title,
        tool2_voiceover=tool2_voiceover,
        f02_voiceover=f02_voiceover,
        illusion_voiceover=illusion_voiceover,
        kit_voiceover=kit_voiceover,
        cta_keyword=cta
    )

    xhs_title = f"千万别直接交！4款AI实测：表面高大上，背地里全是坑！💥"
    xhs_content = f"""网上一堆教你用 AI 做 {topic} 的神仙教程，吹得神乎其神。
作为一个天天在工位实战的打工人，今天我动了真格：
直接把虚构公司的标准业务模板 + 真实数据喂给 4 款顶流工具，提示词死磕“严禁编造”。

结果测评完我一身冷汗：
❌ 有的说做不到，老老实实当大纲战神；
❌ 有的强制绑架只能选自带模板；
❌ 有的导出后把核心标识搞成纯文字占位；
❌ 最可怕的是全员在偷偷捏造业务数据！

⚠️ 职场生存第一定律：
排版不好挨顿批，数据造假背大锅！
AI 负责加速，但终审权必须死死攥在自己手里！

🎁 本期实测的所有测试集、提示词核对单和勾叉总表都整理好了。
需要的同学在评论区扣【{cta}】自取！建议先【收藏】防走丢！"""

    bili_title = f"【硬核实测】把真实业务喂给 4 款顶流 AI，我发现了全员都在偷偷造假！"
    douyin_content = f"把真实业务喂给4款顶流AI，实测结果直接让我惊出一身冷汗！表面排版高大上，背地里居然全员在偷偷造假捏造数据！职场人千万别盲信AI一键生成，AI负责加速，终审权永远在自己手里！完整避坑核对单见评论区！"

    publish_content = PUBLISH_TEMPLATE.format(
        title=title,
        xhs_title=xhs_title,
        xhs_content=xhs_content,
        topic_tag=topic.replace(" ", ""),
        cta_keyword=cta,
        bili_title=bili_title,
        douyin_content=douyin_content
    )

    script_path = output_dir / "script.md"
    publish_path = output_dir / "publish.md"

    script_path.write_text(script_content, encoding="utf-8")
    publish_path.write_text(publish_content, encoding="utf-8")

    print(f"[√] 爆款脚本已生成: {script_path}")
    print(f"[√] 多平台分发文案已生成: {publish_path}")
    return script_path, publish_path


def main():
    parser = argparse.ArgumentParser(description="10分钟爆款脚本生成与抗压蒸馏引擎")
    parser.add_argument("topic", nargs="?", default="AI周报生成", help="测试主题/选题核心")
    parser.add_argument("-t", "--type", choices=["benchmark", "timesaver", "accelerator"], default="benchmark", help="选题类型：benchmark(硬核实测), timesaver(打工人省时间), accelerator(AI加速老赛道)")
    parser.add_argument("-o", "--output-dir", default="./output_project", help="输出项目工程目录")
    parser.add_argument("-c", "--competitor", default="低粉爆款对标", help="对标痛点或竞品")
    parser.add_argument("-e", "--evidence", default="真实数据造假", help="实测冲突证据")
    parser.add_argument("--cta", default="PPT", help="评论区互动领取关键词")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    generate_package(out_dir, args.topic, args.type, args.competitor, args.evidence, args.cta)


if __name__ == "__main__":
    main()
