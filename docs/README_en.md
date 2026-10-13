**| [简体中文](../README.md) | English |**

# AutoMediaEncode (AME)

<div align="center">
  <img src="../app/resource/images/logo_src.png" alt="AME Logo" width="40%">
</div>

AME is a Windows desktop application for media processing, built with PySide6 and [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets).

AME builds on [AutoEncode-V](https://github.com/Dewsweet/AutoEncode-V), bringing key features from its batch scripts—**media information**, **video transcoding**, **media demuxing**, and **media muxing**—to a graphical interface. It also uses [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt) to provide node-based workflows for composing repeatable media processing pipelines.

The project ~~originally started as a personal tool for quickly processing everyday video files without having to memorize CLI commands or constantly look up documentation~~. It now aims to make common media processing tasks simple for users who are less familiar with the command line, while offering more advanced workflow editing for users who are comfortable with it.

Some parts of the project were written with AI assistance. Please report problems through [GitHub Issues](https://github.com/Dewsweet/AutoMediaEncode/issues).

## Features

- **Media information**: View basic media properties and detailed reports with MediaInfo.
- **Media recoding**: Process video, audio, image, and subtitle files with FFmpeg and related tools. Supports x264, x265, SVT-AV1, and selected hardware encoders, with configurable encoding parameters and presets.
- **Media demuxing**: Extract media tracks with mkvextract and FFmpeg. Includes an option to restore subsetted subtitles using font mapping tables.
- **Media muxing**: Package video, audio, subtitle, chapter, and attachment tracks into media files with MKVToolNix (mkvmerge) and FFmpeg.
- **Node-based workflows**: Connect input, track probing, processing, encoding, muxing, and output nodes on a canvas. Workflows can be saved, imported, and exported, and tasks can be run, paused, or cancelled. New users can start with the [AME Node Workflow User Guide](AME%20工作流使用说明.md).
- **Task monitoring**: View task status, processing progress, estimated time remaining, and error details.
- **Interface settings**: Supports Simplified Chinese and English, light and dark themes, accent colors, background images, tool paths, and encoder preset management.

## Installation and Usage

### Download a release

The AME graphical interface is packaged as an executable with Nuitka. Download a release from [GitHub Releases](https://github.com/Dewsweet/AutoMediaEncode/releases), extract it, and run the application. Some media features require additional command-line tools or libraries. Check the release notes, then configure tool paths in the application settings, place tools in the application's `tools/` directory, or add them to your system `PATH`.

### Run from source

AME targets Windows and requires Python 3.10 or later to run from source. A virtual environment is recommended:

```powershell
git clone https://github.com/Dewsweet/AutoMediaEncode.git
Set-Location AutoMediaEncode
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python AutoMediaEncode.py
```

## Acknowledgments

Thanks to the developers of the tools and libraries used by this project:

- [FFmpeg](https://ffmpeg.org/)
- [MediaInfo](https://mediaarea.net/)
- [MKVToolNix](https://mkvtoolnix.download/)
- x264, x265, and SVT-AV1 video encoders
- qaac and FLAC audio encoders
- eac3to

Thanks to the following communities and guides for sharing multimedia processing knowledge:

- [VCB-Studio Guides](https://guides.vcb-s.com/)
- [谜之压制组 Guides](https://iavoe.github.io/)

## License

This project is licensed under the [GPLv3 License](../LICENSE).
