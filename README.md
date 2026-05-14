**| 简体中文 | [English](README_en.md) |**

# AutoMediaEncode

AutoMediaEncode (AME) 是一款基于 PySide6 和 [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 构建的媒体处理现代化 GUI 工具。调用一些命令行程序完成对媒体文件的转码、抽流、混流操作，并计划引入一种节点式的自动化媒体处理工作流 (AME)。

## 主要特性
- **媒体信息**：调用 `Mediainfo` 获取输入文件的基本媒体信息，提供简易和详细两种展示文本。
- **媒体重编码**：调用 `FFmpeg` 对输入视频、音频、图片、字幕进行转码处理。视频支持 H.264/H.265/SVT-AV1 及常见显卡硬件加速编码 (NVENC 等)，可自定义相关 `ffmpeg` 参数。
- **媒体抽流**：参考 `gMKVExtractGUI` 的界面设计，调用 `mkvextract` 和 `ffmpeg` 对视频文件进行轨道提取。内置字幕子集化还原工具，勾选后可将子集化字幕对照字体映射表恢复为正常字幕后导出。
- **媒体混流**：参考 `mkvtoolnix-gui` 的界面设计，调用 `mkvmerge` 和 `ffmpeg` 对输入文件进行混流封装。考虑到 mkvmerge 参数繁多，仅启用了常用选项，有更多功能需求可提交 issues 或使用 mkvtoolnix-gui。
- **任务监控系统**：并行任务队列，以卡片形式实时展示 FFmpeg 进度 (当前进度、总体进度、ETA)，支持健壮的报错与中止保护。
- **个性化与设置**：支持明/暗主题自适应、自定义主题色、自定义背景图片、编码器预设管理、工具路径配置等。

## 开发路线图
- [x] 模块化底层架构 & 任务总控机制
- [x] 主题与个性化设置 & 工具路径管理
- [x] 媒体信息查看
- [x] 媒体重编码
- [x] 媒体抽流
- [x] 媒体混流
- [ ] AME 自动化工作流 (节点式流程编辑器) —— *WIP*

## 安装与运行

### 方法一：Release 下载
GUI 通过 Nuitka 打包构建为可执行文件。你可以在 [Releases](https://github.com/Dewsweet/AutoMediaEncode/releases) 下载压缩包，解压到合理位置即可直接运行。

如果你下载的是非完整包 (不含 CLI 工具)，可自行下载对应程序并放置到软件根目录下的 `tools/` 文件夹中，或添加到系统环境变量。

### 方法二：源码运行
推荐使用 Python 3.10+ 及虚拟环境：

```bash
git clone https://github.com/Dewsweet/AutoMediaEncode.git
cd AutoMediaEncode
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 鸣谢
本项目所用到的相关工具与库，感谢前人的付出：
- [FFmpeg](https://ffmpeg.org/)
- [MediaInfo](https://mediaarea.net/)
- [MKVToolNix](https://mkvtoolnix.download/)
- x264 / x265 / SVT-AV1

感谢以下社区与教程对多媒体处理知识的普及：
- VCB-Studio 公开教程: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 压制教程: [https://iavoe.github.io/](https://iavoe.github.io/)

## 许可协议
本项目遵循 [GPLv3 License](LICENSE) 开源协议。
](https://iavoe.github.io/)
