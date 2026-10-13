**| 简体中文 | [English](docs/README_en.md) |**

# AutoMediaEncode (AME)
<div align="center">
  <img src="app/resource/images/logo_src.png" alt="AME Logo" width="40%">
</div>

AME 是一款面向 Windows 的媒体处理桌面软件，使用 PySide6 和 [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 构建。

可以算是 [AutoEncode-V](https://github.com/Dewsweet/AutoEncode-V) 的 GUI 版/升级版/ ProMax 版，将原本 Batch 脚本中的**媒体信息**、**视频转码**、**视频抽流**、**媒体混流**等重要功能 GUI 实现，并基于 [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt) 实现了节点式工作流，用于编排可重复执行的媒体处理流程。

本项目~~是自用, 原本是不想记忆cli命令和反复查询文档, 用来快速处理日常编辑的视频文件~~。现旨在为不擅长使用命令行的用户提供快速简单的媒体处理功能，同时也为熟悉命令行操作的用户提供较复杂的工作流编辑体验。

由于本人能力有限, 本项目部分代码使用 AI 编写, 有问题也可以提交 [issues](https://github.com/Dewsweet/AutoMediaEncode/issues)。

## 主要功能

- **媒体信息**：使用 MediaInfo 查看媒体文件的基本信息和详细报告。
- **媒体重编码**：通过 FFmpeg 等工具处理视频、音频、图片和字幕；支持 x264、x265、SVT-AV1 及部分硬件编码器，并可设置编码参数和预设。
- **媒体抽流**：使用 mkvextract 和 FFmpeg 提取媒体轨道；支持字幕子集化还原等处理选项。
- **媒体混流**：使用 MKVToolNix（mkvmerge）和 FFmpeg 将视频、音频、字幕、章节及附件等轨道封装到媒体文件中。
- **节点式工作流**：通过画布连接输入、轨道探测、处理、编码、封装和输出节点；支持保存、导入、导出工作流，并可执行、暂停或取消任务。初次上手可以阅读[AME 节点式工作流使用说明](docs/AME%20工作流使用说明.md)。
- **任务监控**：查看任务状态、处理进度和预计剩余时间，并查看错误信息。
- **界面设置**：支持简体中文和英文界面、明暗主题、主题色、背景图片、工具路径及编码器预设管理。


## 安装与运行

### 下载发行版

AME 的图形界面通过 Nuitka 打包为可执行文件。前往 [Releases](https://github.com/Dewsweet/AutoMediaEncode/releases) 下载发行版并解压运行。部分媒体功能需要额外的命令行工具或动态库；请查看发行包说明，并在软件设置中配置工具路径，或将工具放入软件的 `tools/` 目录、加入系统 `PATH`。

### 从源码运行

AME 面向 Windows，源码运行需要 Python 3.10 或更高版本。建议使用虚拟环境：

```powershell
git clone https://github.com/Dewsweet/AutoMediaEncode.git
Set-Location AutoMediaEncode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python AutoMediaEncode.py
```

## 鸣谢
本项目所用到的相关工具与库，感谢前人的付出：
- [FFmpeg](https://ffmpeg.org/)
- [MediaInfo](https://mediaarea.net/)
- [MKVToolNix](https://mkvtoolnix.download/)
- x264、x265、SVT-AV1 视频编码器
- qaac、flac 音频编码器
- eac3to

感谢以下社区与教程对多媒体处理知识的普及：
- VCB-Studio 公开教程: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 压制教程: [https://iavoe.github.io/](https://iavoe.github.io/)

## 许可协议
本项目遵循 [GPLv3 License](LICENSE) 开源协议。
