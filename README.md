**| 简体中文| [English](README_en.md) |**

# AutoMediaEncode (AME)

AutoMediaEncode (AME) 是一款基于 PySide6 和 Fluent Design 风格构建的现代化多媒体处理 GUI 工具。它旨在为有一点基础的用户提供直观、美观且强大的音视频转码、抽流、混流及高级压制管理体验。

## ✨ 核心特性
- **现代且优雅的 UI**：采用 Fluent Design 规范设计，支持系统明/暗主题自适应、自定义主题色以及自定义背景图片。
- **媒体重编码 (Recode)**：
  - **视频**：支持 H.264/AVC, H.265/HEVC, SVT-AV1 以及常见显卡的硬件加速编码 (NVENC 等)。
  - **音频**：支持多种码率控制与常用格式转换。
  - **图片 & 字幕**：支持快速的基础格式转换与处理。
- **编码器预设管理**：内置常用压制参数预设，支持自定义调整，并能将其导出/导入为 JSON 数据。
- **并行监控任务系统**：详尽的任务列表面板，实时测算 FFmpeg 进度 (当前进度、总体进度、ETA)，并提供健壮的报错与中止保护。
- **自包含日志追踪**：内置基于 Loguru 的高级日志系统，保留详细的底层传递与执行参数。

## 🚀 路线图
- [x] 模块化底层架构重构 & 任务总控机制
- [x] 基础媒体重编码 (Recode)
- [x] 主题与个性化设置与工具路径管理
- [ ] 媒体抽流 (Demuxing) -- *WIP*
- [ ] 媒体封装/混流 (Muxing) -- *WIP*
- [ ] 结合 VapourSynth 的高级压制管线 (AutoEncoding)
- [ ] 系统依赖工具 (FFmpeg 等) 的全自动下载与部署

## 🛠️ 安装与运行
1. 克隆本仓库：
   ```bash
   git clone https://github.com/Dewsweet/AutoMediaEncode.git
   cd AutoMediaEncode
   ```
2. 安装所需依赖 (推荐使用 Python 3.10+ 及虚拟环境)：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动 GUI：
   ```bash
   python main.py
   ```
*(注：当前为早期预览阶段，请在使用前确保系统环境中已正确指定 `ffmpeg.exe`)*

## 🤝 鸣谢
感谢以下社区与教程对多媒体处理知识的普及：
- VCB-Studio 公开教程: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 压制教程: [https://iavoe.github.io/](https://iavoe.github.io/)

本项目的界面基于优秀的开源库 [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 构建。

## 📄 许可协议
本项目遵循 [GPLv3 License](LICENSE) 开源协议。
