import subprocess
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from app.services.tool_service import ToolService
from app.common.logger import logger
from app.common.config import cfg, qconfig


class VSPipeNode(AMENodeBase):
    NODE_NAME = 'vspipe'
    DESCRIPTION = 'VapourSynth 管道输出。检测 vspipe API 版本后组装管道命令连接编码器'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Purple']
    INPUTS = [('script', P['script'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'vspipe'

    def execute(self, inputs, temp_dir):
        script = (inputs.get('script') or [''])[0]
        if not script:
            logger.warning('[VSPipe] 没有脚本输入')
            return None

        vspipe_custom = qconfig.get(cfg.vspipe_path)
        vspipe = ToolService.get_tool_path('vspipe', custom_path=vspipe_custom)
        if not vspipe or not Path(vspipe).is_file():
            logger.error('[VSPipe] 找不到 vspipe.exe')
            return None

        api_ver = self._detect_api(vspipe)
        logger.info(f'[VSPipe] vspipe API 版本: {api_ver}')

        if api_ver == '4.0':
            pipe_cmd = f'"{vspipe}" -c y4m "{script}" -'
        else:
            pipe_cmd = f'"{vspipe}" --y4m "{script}" -'

        logger.info(f'[VSPipe] 管道命令: {pipe_cmd}')
        return {'video': [{'cmd': pipe_cmd, 'pipe': True, 'api': api_ver}]}

    def _detect_api(self, vspipe_path):
        try:
            r = subprocess.run(
                [vspipe_path, '-v'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
            output = (r.stdout + r.stderr).lower()
            if 'api4' in output or 'api 4' in output or 'r55' in output or 'r.55' in output:
                return '4.0'
            return '3.0'
        except Exception as e:
            logger.warning(f'[VSPipe] 无法检测版本, 默认 API 3.0: {e}')
            return '3.0'
