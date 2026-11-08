# 03 剪辑与字幕自动化指南

## 一、 静音剔除（Jump Cut）自动化
在录制口播视频时，思考断句、吸气声和重复口误会产生大量无效片段。
- **底层原理**：利用 FFmpeg 的 `silencedetect` 滤镜，扫描音频轨道中音量低于阈值（如 -30dB）且持续超过一定时长（如 0.4 秒）的静音片段，自动切片拼接。
- **推荐执行**：直接运行同目录下提供的 `scripts/cut_silence.py`。

## 二、 本地离线 Whisper 自动打轴与字幕生成
- **核心优势**：无需依赖第三方付费打轴软件，隐私安全且精准度高。
- **基础执行命令**：
  ```bash
  # 使用 faster-whisper 或 openai-whisper
  whisper input_video.mp4 --model medium --language Chinese --output_format srt
  ```
- **字幕校对与敏感词清洗**：
  - 生成 `.srt` 文件后，可由 Agent 快速扫描一轮高频同音字错漏与广告法敏感词（如“最好”、“第一”等违禁词替换为合规表达）。
