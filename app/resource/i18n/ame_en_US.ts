<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="en_US" sourcelanguage="zh_CN">
<context>
    <name>FileLoadInterface</name>
    <message>
        <location filename="../../components/fileload_interface.py" line="+18"/>
        <source>所有文件 (*)</source>
        <translation>All files (*)</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>点击或拖放文件到此区域</source>
        <translation>Click or drop files here</translation>
    </message>
    <message>
        <location line="+9"/>
        <location line="+41"/>
        <source>选择文件</source>
        <translation>Select files</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../../view/main_window.py" line="+111"/>
        <source>媒体信息</source>
        <translation>Media information</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>设置</source>
        <translation>Settings</translation>
    </message>
</context>
<context>
    <name>MediaInfoService</name>
    <message>
        <location filename="../../view/mediainfo_interface.py" line="+33"/>
        <location filename="../../services/mediainfo_service.py" line="+121"/>
        <location line="+23"/>
        <location line="+86"/>
        <source>无法读取媒体信息，请检查文件和 MediaInfo DLL。</source>
        <translation>Could not read media information. Check the file and MediaInfo DLL.</translation>
    </message>
    <message>
        <location filename="../../services/mediainfo_service.py" line="-171"/>
        <location line="+11"/>
        <location line="+16"/>
        <location line="+61"/>
        <location line="+102"/>
        <source>未知</source>
        <translation>Unknown</translation>
    </message>
    <message>
        <location line="-136"/>
        <source>文件不存在，请检查路径是否正确。</source>
        <translation>File not found. Check the path.</translation>
    </message>
    <message>
        <location line="+4"/>
        <source>文件为空，请检查文件是否损坏。</source>
        <translation>The file is empty. Check whether it is damaged.</translation>
    </message>
    <message>
        <location line="+9"/>
        <location line="+116"/>
        <location line="+75"/>
        <source>未添加 MediaInfo DLL, 请确认相关工具路径</source>
        <translation>MediaInfo DLL not found. Check the tool path.</translation>
    </message>
    <message>
        <location line="-65"/>
        <source>**格式: {format}** ; {size}</source>
        <translation>**Format: {format}** ; {size}</translation>
    </message>
    <message>
        <location line="+1"/>
        <location line="+3"/>
        <source>未知格式</source>
        <translation>Unknown format</translation>
    </message>
    <message numerus="yes">
        <location line="+6"/>
        <source>**%n** 个视频流: {codecs}</source>
        <translation>
            <numerusform>**%n** video stream: {codecs}</numerusform>
            <numerusform>**%n** video streams: {codecs}</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location line="+3"/>
        <source>**%n** 个音频流: {codecs}</source>
        <translation>
            <numerusform>**%n** audio stream: {codecs}</numerusform>
            <numerusform>**%n** audio streams: {codecs}</numerusform>
        </translation>
    </message>
    <message numerus="yes">
        <location line="+3"/>
        <source>**%n** 个字幕流: {codecs}</source>
        <translation>
            <numerusform>**%n** subtitle stream: {codecs}</numerusform>
            <numerusform>**%n** subtitle streams: {codecs}</numerusform>
        </translation>
    </message>
    <message>
        <location line="+4"/>
        <source>#### 视频 {index}</source>
        <translation>#### Video {index}</translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+15"/>
        <location line="+10"/>
        <source>- 语言: {language}   </source>
        <translation>- Language: {language}   </translation>
    </message>
    <message>
        <location line="-24"/>
        <source>- 编码格式: {format} ({profile})   </source>
        <translation>- Codec: {format} ({profile})   </translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+30"/>
        <source>- 分辨率: {width} x {height} ({ratio})   </source>
        <translation>- Resolution: {width} x {height} ({ratio})   </translation>
    </message>
    <message>
        <location line="-28"/>
        <source>- 帧率: {rate}   </source>
        <translation>- Frame rate: {rate}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 视频码率: {bitrate}   </source>
        <translation>- Video bit rate: {bitrate}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 位深: {depth}   </source>
        <translation>- Bit depth: {depth}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 色彩抽样: {color}{chroma}   </source>
        <translation>- Color space / chroma subsampling: {color}{chroma}   </translation>
    </message>
    <message>
        <location line="+5"/>
        <source>#### 音频 {index}</source>
        <translation>#### Audio {index}</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>- 编码格式: {format}   </source>
        <translation>- Codec: {format}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 音频码率: {bitrate}   </source>
        <translation>- Audio bit rate: {bitrate}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 采样率: {rate}   </source>
        <translation>- Sampling rate: {rate}   </translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 声道数: {channels}   </source>
        <translation>- Channels: {channels}   </translation>
    </message>
    <message>
        <location line="+4"/>
        <source>#### 字幕 {index}</source>
        <translation>#### Subtitle {index}</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>- 类型: {format}   </source>
        <translation>- Type: {format}   </translation>
    </message>
    <message>
        <location line="+4"/>
        <source>#### 图片 {index}</source>
        <translation>#### Image {index}</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>- 格式: {format}   </source>
        <translation>- Format: {format}   </translation>
    </message>
</context>
<context>
    <name>MediaToolsCardTemplate</name>
    <message>
        <location filename="../../components/tools_template_card.py" line="+68"/>
        <source>软件官网</source>
        <translation>Website</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>工具可用</source>
        <translation>Tool available</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>未找到工具</source>
        <translation>Tool not found</translation>
    </message>
</context>
<context>
    <name>MediaifInterface</name>
    <message>
        <location filename="../../view/mediainfo_interface.py" line="+41"/>
        <source>媒体信息</source>
        <translation>Media information</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>使用 MediaInfo 查询媒体信息</source>
        <translation>Inspect media files with MediaInfo</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>重新载入文件</source>
        <translation>Reload files</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>直接拖入文本框也行✨</source>
        <translation>You can also drop files into the text area ✨</translation>
    </message>
    <message>
        <location line="+2"/>
        <location line="+102"/>
        <source>查看详细信息</source>
        <translation>Show details</translation>
    </message>
    <message>
        <location line="-60"/>
        <source>📌 媒体文件信息 😇</source>
        <translation>📌 Media file information 😇</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>查询媒体文件相关信息</source>
        <translation>Inspect media file information</translation>
    </message>
    <message>
        <location line="+38"/>
        <source>选择文件</source>
        <translation>Select files</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>所有文件 (*)</source>
        <translation>All files (*)</translation>
    </message>
    <message>
        <location line="+23"/>
        <source>正在分析基本媒体信息...</source>
        <translation>Analyzing basic media information...</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>查看基本信息</source>
        <translation>Show summary</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>正在分析完整媒体信息...</source>
        <translation>Analyzing detailed media information...</translation>
    </message>
</context>
<context>
    <name>PresetEditDialog</name>
    <message>
        <location filename="../../components/preset_dialog.py" line="+52"/>
        <source>预设名称 (例如: 日常压制)</source>
        <translation>Preset name (e.g. Everyday encoding)</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>CLI 参数 (例如: --preset veryslow --crf 18 ...)</source>
        <translation>CLI parameters (e.g. --preset veryslow --crf 18 ...)</translation>
    </message>
    <message>
        <location line="+21"/>
        <source>保存</source>
        <translation>Save</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>取消</source>
        <translation>Cancel</translation>
    </message>
</context>
<context>
    <name>PresetManagerDialog</name>
    <message>
        <location line="+17"/>
        <source>{encoder} 预设</source>
        <translation>{encoder} presets</translation>
    </message>
    <message>
        <location line="+44"/>
        <source>添加</source>
        <translation>Add</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>默认</source>
        <translation>Defaults</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>应用</source>
        <translation>Apply</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>取消</source>
        <translation>Cancel</translation>
    </message>
    <message>
        <location line="+40"/>
        <source>新建预设</source>
        <translation>New preset</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>编辑: {name}</source>
        <translation>Edit: {name}</translation>
    </message>
</context>
<context>
    <name>SettingInterface</name>
    <message>
        <location filename="../../view/setting_interface.py" line="+47"/>
        <source>设置</source>
        <translation>Settings</translation>
    </message>
    <message>
        <location line="+11"/>
        <source>工具选项</source>
        <translation>Tools</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>媒体工具</source>
        <translation>Media tools</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>本软件所用到的基本媒体处理工具</source>
        <translation>Tools used by AME for media processing</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>刷新工具状态</source>
        <translation>Refresh tool status</translation>
    </message>
    <message>
        <location line="+8"/>
        <source>打开工具文件夹</source>
        <translation>Open tools folder</translation>
    </message>
    <message>
        <location line="+36"/>
        <source>编码器预设</source>
        <translation>Encoder presets</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>基础编码器相关参数的预设</source>
        <translation>Manage command-line presets for supported encoders</translation>
    </message>
    <message>
        <location line="+4"/>
        <source>导出所有预设</source>
        <translation>Export all presets</translation>
    </message>
    <message>
        <location line="+14"/>
        <source>H.264/AVC 编码器</source>
        <translation>H.264/AVC encoder</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>H.265/HEVC 编码器</source>
        <translation>H.265/HEVC encoder</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>SVT-AV1 编码器</source>
        <translation>SVT-AV1 encoder</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>个性化</source>
        <translation>Personalization</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>语言 (Language)</source>
        <translation>Language</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>选择软件的显示语言</source>
        <translation>Choose the display language for AME</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>系统默认</source>
        <translation>Use system language</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>应用主题</source>
        <translation>App theme</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>调整你的应用外观</source>
        <translation>Change the appearance of AME</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>浅色</source>
        <translation>Light</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>深色</source>
        <translation>Dark</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>跟随系统设置</source>
        <translation>Use system setting</translation>
    </message>
    <message>
        <location line="+7"/>
        <source>主题颜色</source>
        <translation>Accent color</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>自定义你的主题颜色</source>
        <translation>Choose a custom accent color</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>选择图片</source>
        <translation>Choose image</translation>
    </message>
    <message>
        <location line="+2"/>
        <source>自定义背景图片</source>
        <translation>Background image</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>清除背景图片</source>
        <translation>Clear background image</translation>
    </message>
    <message>
        <location line="+7"/>
        <location line="+26"/>
        <source>关于</source>
        <translation>About</translation>
    </message>
    <message>
        <location line="-24"/>
        <source>帮助</source>
        <translation>Help</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>使用说明和常见问题</source>
        <translation>User guide and frequently asked questions</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>本软件旨在为不擅长使用命令行的用户提供快速简单的媒体处理功能，同时也为熟悉命令行操作的用户提供较复杂的工作流编辑体验</source>
        <translation>AME makes media processing quick and simple for users unfamiliar with command-line tools, while offering an advanced workflow editor for experienced users</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>感谢VCB-Studio和谜之压制组的开源, 关于媒体处理和编码器可以参考他们的教程:</source>
        <translation>Thanks to VCB-Studio and Iavoe for their open-source contributions. Learn more about media processing and encoding in their guides:</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>谜之压制组 压制教程: https://iavoe.github.io/</source>
        <translation>Iavoe encoding guide: https://iavoe.github.io/</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>VCB-Studio 公开教程: https://guides.vcb-s.com/</source>
        <translation>VCB-Studio guides: https://guides.vcb-s.com/</translation>
    </message>
    <message>
        <location line="+13"/>
        <location line="+282"/>
        <source>检查更新</source>
        <translation>Check for updates</translation>
    </message>
    <message>
        <location line="-279"/>
        <source>© 版权所有 {year}, {author}. 版本 {version}</source>
        <translation>© Copyright {year}, {author}. Version {version}</translation>
    </message>
    <message>
        <location line="+103"/>
        <source>语言设置已保存</source>
        <translation>Language preference saved</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>将在下次启动时生效</source>
        <translation>It will take effect the next time you start the app</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>默认纯色</source>
        <translation>Default solid color</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>让程序界面更加花里胡哨😋 (当前: {name})</source>
        <translation>Give AME a personal touch 😋 (Current: {name})</translation>
    </message>
    <message>
        <location line="+19"/>
        <source>选择 vspipe</source>
        <translation>Choose vspipe</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>可执行文件 (*.exe);;所有文件 (*.*)</source>
        <translation>Executable files (*.exe);;All files (*.*)</translation>
    </message>
    <message>
        <location line="+16"/>
        <source>错误: 选定的文件不是 vspipe 程序, 请检查文件名</source>
        <translation>Error: The selected file is not vspipe. Check the file name</translation>
    </message>
    <message>
        <location line="+11"/>
        <source>导出预设</source>
        <translation>Export presets</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>JSON 文件 (*.json)</source>
        <translation>JSON files (*.json)</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>导出成功</source>
        <translation>Export complete</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>预设已成功导出</source>
        <translation>Presets exported successfully</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>导出失败</source>
        <translation>Export failed</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>错误信息：{detail}</source>
        <translation>Error details: {detail}</translation>
    </message>
    <message>
        <location line="+18"/>
        <source>选择背景图片</source>
        <translation>Choose background image</translation>
    </message>
    <message>
        <location line="+0"/>
        <source>图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)</source>
        <translation>Image files (*.png *.jpg *.jpeg *.bmp);;All files (*.*)</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>请稍候</source>
        <translation>Please wait</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>正在检查更新，请勿重复操作</source>
        <translation>Checking for updates. Please wait before trying again</translation>
    </message>
    <message>
        <location line="+11"/>
        <source>检查中....</source>
        <translation>Checking....</translation>
    </message>
    <message>
        <location line="+23"/>
        <source>版本检查</source>
        <translation>Version check</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>远程版本 ({remote}) 低于当前版本 ({current})，无需更新</source>
        <translation>The available version ({remote}) is older than your version ({current}). No update is needed</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>已是最新版本</source>
        <translation>Up to date</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>当前版本 ({version}) 已是最新</source>
        <translation>Your version ({version}) is up to date</translation>
    </message>
    <message>
        <location line="+12"/>
        <source>检查更新失败</source>
        <translation>Update check failed</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>{reason}，可稍后重试</source>
        <translation>{reason}. Please try again later</translation>
    </message>
</context>
<context>
    <name>ToolDescriptions</name>
    <message>
        <location filename="../../services/tool_service.py" line="+19"/>
        <source>领先的多媒体框架</source>
        <translation>A leading multimedia framework</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>媒体文件信息分析工具</source>
        <translation>Media file information analyzer</translation>
    </message>
    <message>
        <location line="+15"/>
        <source>MKV 混流工具</source>
        <translation>Matroska muxing tools</translation>
    </message>
    <message>
        <location line="+14"/>
        <source>H.264 视频编码器</source>
        <translation>H.264 video encoder</translation>
    </message>
    <message>
        <location line="+14"/>
        <source>H.265 视频编码器</source>
        <translation>H.265 video encoder</translation>
    </message>
    <message>
        <location line="+13"/>
        <source>SVT-AV1 视频编码器</source>
        <translation>SVT-AV1 video encoder</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>AAC 音频编码器，基于 Apple 的 CoreAudio</source>
        <translation>AAC audio encoder based on Apple&apos;s CoreAudio</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>Blu-ray/HD DVD 轨道探测与无损提取工具</source>
        <translation>Blu-ray/HD DVD track detection and lossless extraction</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>强大的视频处理框架; 不影响软件的基本功能, 有需要请自行指定位置</source>
        <translation>Advanced video processing framework; optional for basic features. Set its path if needed</translation>
    </message>
</context>
<context>
    <name>UpdateCheckWorker</name>
    <message>
        <location filename="../../services/update_service.py" line="+45"/>
        <source>仓库中暂无可用版本</source>
        <translation>No releases are available in the repository</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>服务器返回错误 (HTTP {code})</source>
        <translation>The server returned an error (HTTP {code})</translation>
    </message>
    <message>
        <location line="+4"/>
        <source>无法连接 GitHub，请检查网络连接或代理设置</source>
        <translation>Cannot connect to GitHub. Check your network connection or proxy settings</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>响应数据解析失败</source>
        <translation>Could not parse the response data</translation>
    </message>
    <message>
        <location line="+3"/>
        <source>未知错误: {detail}</source>
        <translation>Unknown error: {detail}</translation>
    </message>
</context>
<context>
    <name>UpdateDialog</name>
    <message>
        <location filename="../../components/update_dialog.py" line="+31"/>
        <source>发现新版本</source>
        <translation>New version available</translation>
    </message>
    <message>
        <location line="+5"/>
        <source>当前版本</source>
        <translation>Current version</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>最新版本</source>
        <translation>Latest version</translation>
    </message>
    <message>
        <location line="+10"/>
        <source>更新日志</source>
        <translation>Release notes</translation>
    </message>
    <message>
        <location line="+6"/>
        <source>（无更新日志）</source>
        <translation>(No release notes)</translation>
    </message>
    <message>
        <location line="+22"/>
        <source>前往下载</source>
        <translation>Download</translation>
    </message>
    <message>
        <location line="+1"/>
        <source>以后再说</source>
        <translation>Later</translation>
    </message>
    <message>
        <location line="+9"/>
        <source>发布于</source>
        <translation>Published</translation>
    </message>
</context>
</TS>
