---
name: creator-studio
description: >-
  全流程自媒体创作者工作流（Creator Studio）。当用户提到自媒体、短视频创作、选题调研、脚本分镜打磨、视频粗剪/字幕、多平台分发或数据复盘时使用。该技能内置交互式下拉执行门禁，支持全流程各环节的快速代操与执行。
---

# Creator Studio · 自媒体全链路作战工作流

本技能为自媒体（短视频、图文、长视频）全生命周期提供体系化支持。涵盖从灵感选题到发布复盘的完整链路，支持交互式选择与全自动动手代操。

---

## 阶段一：交互式下拉执行门禁（强制先验）

当该技能被触发时，**不要直接假设用户需求并堆砌长篇文字**。必须优先使用 `ask_question` 工具向用户抛出交互式单选下拉菜单，列出具体可执行的作战动作：

```json
{
  "questions": [
    {
      "question": "请从下方选择你要执行的 Creator Studio 作战动作：",
      "options": [
        "(Recommended) 🎬 一键流水线总装 (pipeline.py: 压制-14 LUFS + 封面截帧 + 飞书入库)",
        "📝 10分钟爆款脚本生成 (generate_script.py: 传入选题生成短句重音脚本与三平台文案)",
        "🎨 预渲染高清对比卡片 (render_cards.py: 批量输出 1080x1920 动效图)",
        "✂️ 智能切除口播气口 (silence.py: 苹果硬件加速秒切停顿倒吸气)",
        "📊 发后数据体检与复盘 (review.py: 赞播比/赞藏比/90天推荐池/P0诊断)",
        "☁️ 单独同步飞书多维表格 (feishu_sync.py: 本地物料与云端总表同步)"
      ],
      "is_multi_select": false
    }
  ]
}
```

---

## 阶段二：选择后立即执行对应作业

用户选定对应动作后，Agent 立即定位目标工程目录（未指定时默认最新的工程或当前目录），并直接运行对应的底座脚本：

### 1. 🎬 一键流水线总装
运行 `pipeline.py <工程目录>`：
- 执行 `ffmpeg-skill` 响度标准化（`-14 LUFS` 对齐）；
- 执行 `oil-cover` 自动截取 8 候选帧与封面排版方案；
- 执行 `feishu_sync.py` 将最新物料状态推入飞书多维表格。

### 2. 📝 10分钟爆款脚本生成
运行 `generate_script.py <选题名称> -t <类型> -o <输出目录>`：
- 自动生成符合黄金 3 秒开门狠话、短句重音标点、画中画运镜指令的 `script.md`；
- 自动生成小红书大字报痛点版、B站深度横评版、抖音/视频号横屏版的 `publish.md`。

### 3. 🎨 预渲染高清对比卡片
运行 `render_cards.py <工程目录>`：
- 基于 Playwright 自动渲染 1080x1920 竖版或横版的高保真红绿勾叉表、数字对比胶囊与代码终端卡片，生成至 `delivery/cards/`。

### 4. ✂️ 智能切除口播气口
运行 `silence.py <视频文件> -o <输出文件> --threshold -35 --hw`：
- 针对原始口播视频，使用苹果 VideoToolbox 硬件加速切除 0.6 秒以上的无声停顿与倒吸气。

### 5. 📊 发后数据体检与复盘
运行 `review.py <工程目录> --views <播放量> --likes <点赞> --saves <收藏> --bounce2s <跳出率> --retention5s <完播率>`：
- 自动计算赞播比与赞藏比；
- 判定是否命中“横屏中长视频 90 天长效推荐池”；
- 输出 🔴 P0 / 🟠 P1 / 🟡 P2 级别体检报告 `review.md`，给出下周周中改进动作。

### 6. ☁️ 单独同步飞书多维表格
运行 `feishu_sync.py <工程目录>`：
- 秒级同步本地工程状态、分镜完成度、核心痛点与产物清单至飞书多维表格「AI自媒体自动化·选题与出片总表」。

---

## 参考方法论与实战指南
- [01 选题与对标侦察指南](./references/01_topic_research.md)
- [02 脚本与分镜抗压指南](./references/02_script_storyboard.md)
- [03 剪辑与字幕优化指南](./references/03_editing_workflow.md)
- [04 发布分发与数据复盘指南](./references/04_distribution_analytics.md)
- [05 六年自媒体老兵核心实战铁律](./references/05_veteran_rules.md)
