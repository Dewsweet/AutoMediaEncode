import subprocess, shlex, re, time
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CLITextWidget, CustomTextWidget
from app.services.tool_service import ToolService
from app.services.error_service import ErrorService
from app.common.logger import logger

class FFmpegProcessorWidget(CustomTextWidget):
    def __init__(self, parent, name, placeholder={}):
        super().__init__(parent, name, placeholder)
        self.set_lebal_text('FFmpeg 命令行参数: ')
        self.set_btn_name('插入')
        self.set_text('-i {input} -c:v libx264 -preset veryslow -crf 18 {output}.mkv')
        self.set_text_placeholder('在这输入 FFmpeg 命令行参数，使用 插入 来添加输入/输出占位符')
        self.set_text_height(120)

class FFmpegProcessorNode(AMENodeBase):
    NODE_NAME = 'FFmpeg CLI'
    DESCRIPTION = '自定义 FFmpeg 命令行处理'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Orange']
    INPUTS = [('input_1', P['any']), ('input_2', P['any']), ('input_3', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'ffmpeg_processor'

    def _setup_widgets(self):
        plachholder = {
            '输入文件': '{input}',
            '使用 image2 分离器': '{image2}', 
            '使用 concat  分离器': '{concat_list}',
            '输出文件路径': '{output}',
        }
        self.add_custom_widget(FFmpegProcessorWidget(self.view, 'ffmpeg_processor', placeholder=plachholder))

    def execute(self, inputs, temp_dir):
        logger.info('\n' + '='*40 + f' [{self.NODE_NAME}] ' + '='*40)

        # 1. 扁平化收集所有端口的输入文件
        all_files = []
        for port_name, _ in self.INPUTS:
            port_files = inputs.get(port_name, [])
            if isinstance(port_files, list):
                all_files.extend(port_files)
            elif port_files:
                all_files.append(port_files)

        if not all_files:
            logger.warning(f'[{self.NODE_NAME}] 没有输入文件，跳过处理')
            return None

        all_files = [Path(f) for f in all_files]

        # 2. 检查 FFmpeg 环境
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff:
            logger.error(f'[{self.NODE_NAME}] 找不到 ffmpeg 可执行文件')
            return None

        cli_text = self.property('ffmpeg_processor', '').strip()
        if not cli_text:
            logger.error(f'[{self.NODE_NAME}] 命令行参数为空')
            return None
        if '{output}' not in cli_text:
            logger.error(f'[{self.NODE_NAME}] 缺少 {{output}} 占位符。示例: -c:v copy {{output}}.mkv')
            return None

        # 3. 预处理 {concat_list}
        concat_txt = None
        if '{concat_list}' in cli_text:
            concat_txt = Path(temp_dir) / f'concat_{self.id}.txt'
            with open(concat_txt, 'w', encoding='utf-8') as f:
                for src in all_files:
                    f.write(f"file '{src.as_posix()}'\n")

        # 4. 预处理 {image2} (自动推断序列格式，如 img_%03d.png)
        image2_path_str = ""
        if '{image2}' in cli_text:
            first_file = all_files[0]
            # 正则提取文件名末尾的数字 (如 frame_001.png -> 提取出 001)
            match = re.search(r'(\d+)$', first_file.stem)
            if match:
                digits = match.group(1)
                pad_len = len(digits)
                # 拼接成 FFmpeg 支持的通配符格式
                seq_pattern = f"%0{pad_len}d"
                new_stem = first_file.stem[:match.start()] + seq_pattern
                # 使用 as_posix 避免反斜杠在 FFmpeg 内部被转义吃掉
                image2_path_str = (first_file.parent / (new_stem + first_file.suffix)).as_posix()
                logger.info(f"[{self.NODE_NAME}] 自动推断 image2 序列格式: {image2_path_str}")
            else:
                logger.warning(f"[{self.NODE_NAME}] image2 推断失败: 文件名末尾未找到数字 ({first_file.name})")
                image2_path_str = first_file.as_posix()

        # 5. shlex 解析命令文本 (防御空格路径炸断命令)
        try:
            cli_parts = shlex.split(cli_text)
        except ValueError:
            cli_parts = cli_text.split()

        cmd = [str(ff)]
        base_out = Path(temp_dir) / f'ff_out_{self.id}'
        final_out_path = None
        input_regex = re.compile(r'\{input_(\d+)\}') # 匹配 {input_0}, {input_1} 等占位符

        # 6. 对解析后的参数块逐个执行占位符替换
        for part in cli_parts:
            # 替换分离器相关的
            if concat_txt and '{concat_list}' in part:
                part = part.replace('{concat_list}', str(concat_txt))
            if image2_path_str and '{image2}' in part:
                part = part.replace('{image2}', image2_path_str)

            # 替换基础 {input} (映射为第 0 个文件)
            if '{input}' in part:
                part = part.replace('{input}', str(all_files[0]))

            # 替换带序列的 {input_0}, {input_1}...
            def replace_input(match):
                idx = int(match.group(1))
                if idx < len(all_files):
                    return str(all_files[idx])
                else:
                    logger.warning(f"[{self.NODE_NAME}] 占位符 {{input_{idx}}} 超出输入文件总数")
                    return match.group(0)
            
            part = input_regex.sub(replace_input, part)

            # 替换输出路径 {output}
            if '{output}' in part:
                part = part.replace('{output}', str(base_out))
                final_out_path = Path(part)
                # 防死锁：如果目标文件已存在先删除它
                if final_out_path.exists(): final_out_path.unlink()

            cmd.append(part)

        if '-y' not in cmd:
            cmd.insert(1, '-y')

        # 7. 轮询执行
        logger.info(f'[{self.NODE_NAME}] 执行命令: {" ".join(cmd)}')
        cf = subprocess.CREATE_NO_WINDOW
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                text=True, encoding='utf-8', errors='replace', creationflags=cf, bufsize=1)
        
        output_lines = []
        cancelled = getattr(self, '_ame_cancelled', lambda: False)
        paused = getattr(self, '_ame_paused', None)

        for line in proc.stdout:
            output_lines.append(line.strip())
            # 相应工作流的取消和暂停请求
            if paused and paused():
                while paused():
                    time.sleep(0.1)
                    if cancelled():
                        proc.terminate(); proc.wait(3); return None
            if cancelled():
                proc.terminate(); proc.wait(3); return None

        proc.wait()

        # 8. 清理临时 concat 列表
        # if concat_txt and concat_txt.exists():
        #     concat_txt.unlink() 

        if proc.returncode == 0 and final_out_path and final_out_path.is_file() and final_out_path.stat().st_size > 0:
            logger.info(f'[{self.NODE_NAME}] 处理成功: {final_out_path.name}')
            return {'output': [str(final_out_path)]}
        else:
            logger.error(f'[{self.NODE_NAME}] 处理失败: returncode={proc.returncode}')
            err_text = "\n".join(output_lines[-10:]) if output_lines else "无输出"
            self._last_error = ErrorService.ffmpeg_error(err_text)
            return None