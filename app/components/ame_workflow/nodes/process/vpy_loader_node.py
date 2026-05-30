import re, shutil
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget
from app.common.logger import logger

# 已知 VapourSynth 源滤镜正则 (前缀+路径+引号)
SOURCE_PATTERNS = [
    r"(core\.lsmas\.LibavSMASHSource\s*\(\s*['\"]r?)",
    r"(core\.lsmas\.LWLibavSource\s*\(\s*['\"]r?)",
    r"(core\.ffms2\.Source\s*\(\s*['\"]r?)",
    r"(core\.d2v\.Source\s*\(\s*['\"]r?)",
    r"(core\.dgdecodenv\.DGSource\s*\(\s*['\"]r?)",
    r"(core\.avisource\.AVIFileSource\s*\(\s*['\"]r?)",
]


class VPYLoaderNode(AMENodeBase):
    NODE_NAME = 'vpy加载器'
    DESCRIPTION = '载入 .vpy 脚本，自动替换 __INPUT_FILE__ 或匹配源滤镜路径'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Purple']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('script', P['script'])]
    MENU_KEY = 'vpy_loader'

    def _setup_widgets(self):
        self.add_custom_widget(FileBrowseWidget(self.view, 'vpy_path', '选择vpy', exts='VPY (*.vpy);;All (*)'))

    def execute(self, inputs, temp_dir):
        vpy_src = self.property('vpy_path', '')
        if not vpy_src:
            logger.warning('[VPYLoader] 没有选择 vpy 脚本')
            return None
        
        inp_list = inputs.get('input', [])
        inp_str = inp_list[0] if inp_list else ''
        inp = Path(inp_str)
        if not inp.is_file():
            logger.warning(f'[VPYLoader] 输入视频不存在: {inp}')
            return None

        # 复制输入文件到临时目录
        upstream = Path(temp_dir) / inp.name
        if upstream.resolve() != inp.resolve():
            try:
                shutil.copy2(inp, upstream) # 复制到临时目录，确保路径可访问且不锁定源文件
            except Exception as e:
                logger.error(f'[VPYLoader] 复制文件失败: {e}')
                return None

        vpy_path = Path(vpy_src)
        if not vpy_path.is_file():
            logger.error(f'[VPYLoader] vpy 文件不存在: {vpy_path}')
            return None

        content = vpy_path.read_text(encoding='utf-8')
        # VapourSynth 统一使用正斜杠最安全，避免 Python 字符串转义错误
        new_path = str(upstream).replace('\\', '/')

        # 占位符精确替换
        if '__INPUT_FILE__' in content:
            content = content.replace('__INPUT_FILE__', new_path)
            logger.info('[VPYLoader] 替换 __INPUT_FILE__ 占位符')
        else:
            # 如果没有占位符但有上游输入，则尝试正则替换已知源滤镜路径
            replaced = False
            for pat_prefix in SOURCE_PATTERNS:
                full_pat = pat_prefix + r"([^'\"]+)(['\"])"
                if re.search(full_pat, content):
                    # 使用 \g<1> 避免 new_path 包含数字（如 123.mp4）时 \1 解析成 \1123 的分组越界错误
                    content = re.sub(full_pat, rf"\g<1>{new_path}\g<3>", content, count=1)
                    logger.info(f'[VPYLoader] 正则替换源滤镜路径: {pat_prefix[:40]}...')
                    replaced = True
                    break
            if not replaced:
                logger.warning('[VPYLoader] 脚本中未找到 __INPUT_FILE__ 或已知源滤镜，保留原样')

        dst = Path(temp_dir) / f'script_{self.id}.vpy'
        dst.write_text(content, encoding='utf-8')
        logger.info(f'[VPYLoader] 输出脚本: {dst}')
        return {'script': [str(dst)]}
