**| [简体中文](README.md) | English |**

# AutoMediaEncode (AME)

AutoMediaEncode (AME) is a modern multimedia processing GUI tool built with PySide6 and Fluent Design. It aims to provide intuitive, beautiful, and powerful media transcoding, demuxing, muxing, and advanced encoding management for users with some foundational knowledge.

### ✨ Features
- **Modern & Elegant UI**: Built with Fluent Design specifications, supporting light/dark themes, custom accent colors, and custom background images.
- **Media Recoding (Recode)**:
  - **Video**: Supports H.264/AVC, H.265/HEVC, SVT-AV1, and hardware-accelerated encoding (e.g., NVENC).
  - **Audio/Images/Subtitles**: Basic format conversions and quick processing.
- **Preset Management**: Built-in encoding presets, customizable options, and the ability to export/import configurations as JSON.
- **Task Management & Monitoring**: Detailed task lists with real-time FFmpeg progress tracking (overall progress, ETA) and robust error handling.
- **Advanced Logging**: Powered by Loguru for detailed tracking and easy debugging.

### 🚀 Roadmap
- [x] Modular architecture & Task dispatcher bus decoupling
- [x] Basic Media Recoding
- [x] Theming, customization, and tool path management
- [ ] Media Demuxing -- *WIP*
- [ ] Media Muxing -- *WIP*
- [ ] Advanced encoding pipeline integrating VapourSynth
- [ ] Automatic background download/deployment of tool dependencies

### 🛠️ Installation & Usage
1. Clone the repository:
   ```bash
   git clone https://github.com/Dewsweet/AutoMediaEncode.git
   cd AutoMediaEncode
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### 🤝 Acknowledgments
Thanks to the following communities for sharing multimedia processing knowledge:
- VCB-Studio Guides: [https://guides.vcb-s.com/](https://guides.vcb-s.com/)
- 谜之压制组 Guides: [https://iavoe.github.io/](https://iavoe.github.io/)

The UI is built upon the excellent [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) library.

### 📄 License
This project is licensed under the [GPLv3 License](LICENSE).
