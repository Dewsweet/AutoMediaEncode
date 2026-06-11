**| [简体中文](README.md) | English |**

# AutoMediaEncode(AME)
<div align="center">
  <img src="app/resource/images/logo_src.png" alt="AME Preview" width="40%">
</div>

AME is a modern multimedia processing GUI tool built with PySide6 and [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets).

It can be considered the GUI version / upgrade / ProMax version of [AutoEncode-V](https://github.com/Dewsweet/AutoEncode-V), migrating the **Media Info**, **Video Transcoding**, **Video Demuxing**, and **Media Muxing** features from the original Batch scripts into a GUI, while also implementing a node-based workflow via [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt).

This project ~~was originally for personal use, to avoid memorizing CLI commands and constantly referencing documentation for quick processing of daily video files~~. It now aims to provide fast and simple media processing for users unfamiliar with the command line, while also offering a more complex workflow editing experience for users comfortable with CLI operations.

Since my abilities are limited, parts of this project were written with AI assistance. Issues can be submitted via [issues](https://github.com/Dewsweet/AutoMediaEncode/issues).

## Features
- [x] **Media Info**: Uses `Mediainfo` to retrieve basic media information from input files, with both simple and detailed view modes.
- [x] **Media Recoding**: Transcodes video, audio, image, and subtitle files via `FFmpeg`. Video encoding supports H.264/H.265/SVT-AV1 and common GPU hardware acceleration (NVENC, etc.), with customizable `ffmpeg` parameters.
- [x] **Media Demuxing**: Designed after `gMKVExtractGUI`, extracts tracks from video files using `mkvextract` and `ffmpeg`. Includes a built-in subtitle de-subsetting tool that restores subset fonts to their normal form based on font mapping tables during extraction.
- [x] **Media Muxing**: Designed after `mkvtoolnix-gui`, muxes input files into containers using `mkvmerge` and `ffmpeg`. Only the most common mkvmerge options are exposed; submit an issue for additional feature requests or use mkvtoolnix-gui.
- [x] **Node-based Workflow**: A node-based workflow editor built on NodeGraphQt, allowing modular orchestration of transcoding, demuxing, muxing, and other functions. Basic media encoding processing is now fully implemented, with more node types to follow.
- [x] **Task Monitoring System**: Parallel task queue with real-time FFmpeg progress displayed as cards (current progress, overall progress, ETA), with robust error handling and cancellation protection.
- [x] **Personalization & Settings**: Supports light/dark theme adaptation, custom accent colors, custom background images, encoder preset management, and tool path configuration.

## Installation & Usage

### Option 1: Download Release
The GUI is packaged as an executable via Nuitka. Download the archive from [Releases](https://github.com/Dewsweet/AutoMediaEncode/releases), extract it to a suitable location, and run the executable directly.

If you download a non-full package (without CLI tools), download the corresponding programs separately and place them in the `tools/` directory under the application root, or add them to your system PATH.

### Option 2: Run from Source
Python 3.10+ and a virtual environment are recommended:

```bash
git clone https://github.com/Dewsweet/AutoMediaEncode.git
cd AutoMediaEncode
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Acknowledgments
Thanks to the following tools and libraries for making this project possible:
- [FFmpeg](https://ffmpeg.org/)
- [MediaInfo](https://mediaarea.net/)
- [MKVToolNix](https://mkvtoolnix.download/)
- x264 / x265 / SVT-AV1

Thanks to the following communities for sharing multimedia processing knowledge:
- VCB-Studio Guides: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 Guides: [https://iavoe.github.io/](https://iavoe.github.io/)

## License
This project is licensed under the [GPLv3 License](LICENSE).
