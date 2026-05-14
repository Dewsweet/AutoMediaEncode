**| [简体中文](README.md) | English |**

# AutoMediaEncode

AutoMediaEncode (AME) is a modern multimedia processing GUI tool built with PySide6 and [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets). It provides an intuitive interface for media transcoding, demuxing, and muxing via various CLI tools, with a planned node-based automated media workflow (AME).

## Features
- **Media Info**: Uses `Mediainfo` to display file metadata, with both simple and detailed view modes.
- **Media Recoding**: Transcodes video, audio, image, and subtitle files via `FFmpeg`. Video encoding supports H.264/H.265/SVT-AV1 and hardware-accelerated codecs (NVENC, etc.), with customizable `ffmpeg` parameters.
- **Media Demuxing**: Designed after `gMKVExtractGUI`, extracts individual tracks from media files using `mkvextract` and `ffmpeg`. Includes a built-in subtitle de-subsetting tool that restores subset fonts to their original form during extraction.
- **Media Muxing**: Designed after `mkvtoolnix-gui`, muxes input files into a single container using `mkvmerge` and `ffmpeg`. Only the most common mkvmerge options are exposed; use mkvtoolnix-gui for advanced features or submit an issue.
- **Task Monitoring**: Parallel task queue with real-time progress cards showing FFmpeg progress (current, overall, ETA), with robust error handling and cancellation support.
- **Personalization & Settings**: Supports light/dark theme adaptation, custom accent colors, custom background images, encoder preset management, and tool path configuration.

## Roadmap
- [x] Modular architecture & task dispatcher system
- [x] Theming, personalization, & tool path management
- [x] Media Info viewer
- [x] Media Recoding
- [x] Media Demuxing
- [x] Media Muxing
- [ ] AME automated workflow (node-based pipeline editor) —— *WIP*

## Installation & Usage

### Option 1: Download Release
Pre-built executables are packaged via Nuitka. Download the latest archive from [Releases](https://github.com/Dewsweet/AutoMediaEncode/releases), extract it to a suitable location, and run the executable.

If the package does not include CLI tools, download them separately and place them in the `tools/` directory under the application root, or add them to your system PATH.

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
Thanks to the following tools and libraries:
- [FFmpeg](https://ffmpeg.org/)
- [MediaInfo](https://mediaarea.net/)
- [MKVToolNix](https://mkvtoolnix.download/)
- x264 / x265 / SVT-AV1

Thanks to the following communities for sharing multimedia processing knowledge:
- VCB-Studio Guides: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 Guides: [https://iavoe.github.io/](https://iavoe.github.io/)

## License
This project is licensed under the [GPLv3 License](LICENSE).
