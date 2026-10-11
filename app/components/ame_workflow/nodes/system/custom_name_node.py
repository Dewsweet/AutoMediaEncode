from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
import re
import shutil
from pathlib import Path
from datetime import datetime
from app.services.output_service import safe_filename
from app.services.ame_workflow.process_runner import check_cancelled, ProcessCancelled
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CustomTextWidget, SwitchButtonWidget, CheckBoxWidget
from app.common.logger import logger

class CustomNameNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '自定义文件名')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", '重命名文件。{input_name} 替换为输入文件名(不含扩展名)，{datetime} 替换为当前时间')
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('file', P['any'])]
    OUTPUTS = [('file', P['any'])]
    MENU_KEY = 'custom_name'

    def _setup_widgets(self):
        placeholders = {
            QCoreApplication.translate('AMENodes', '输入文件名'): '{input_name}',
            QCoreApplication.translate('AMENodes', '日期时间'): '{datetime}',
            QCoreApplication.translate('AMENodes', '序列化'): '{index:00}',
            }
        self.add_custom_widget(CustomTextWidget(self.view, 'custom_name', placeholder=placeholders))
        self.add_custom_widget(CheckBoxWidget(self.view, 'copy2_temp', QCoreApplication.translate('AMENodes', '复制文件到缓存目录')))

    def execute(self, inputs, temp_dir):
        logger.info('\n' * 2 + '=' * 40 + f' [{self.NODE_NAME}] ' + '=' * 40)
        
        raw_files = inputs.get('file', [])
        if not raw_files:
            return None
            
        files = sorted([Path(f) for f in raw_files])
        
        custom_text = self.property('custom_name', '')
        # 获取用户是否开启了复制选项
        is_copy = self.property('copy2_temp', False)

        if not custom_text:
            # 如果没有输入重命名规则，但选择了复制，也应该执行复制逻辑
            if not is_copy:
                return {'file': [str(f) for f in files]}
            else:
                custom_text = '{input_name}'

        now_text = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = []
        plan = []
        reserved = set()
        if is_copy and (not temp_dir or not Path(temp_dir).is_dir()):
            self._last_error = QCoreApplication.translate('AMENodes', '缓存目录无效，无法复制文件')
            return None

        for i, src in enumerate(files, start=1):
            name = custom_text
            
            # 1. 替换基础占位符
            name = name.replace('{input_name}', src.stem)
            name = name.replace('{datetime}', now_text)
            
            # 2. 动态解析 {index:00} 系列占位符
            def index_replacer(match):
                zeros = match.group(1)
                width = len(zeros) if zeros else 1
                return f"{i:0{width}d}"
            name = re.sub(r'\{index:?(0*)\}', index_replacer, name)

            # 3. 处理扩展名
            if '{ext}' in name:
                name = name.replace('{ext}', src.suffix.lstrip('.'))
            else:
                name = name + src.suffix

            # 4. 核心逻辑：确定目标所在的文件夹
            target_folder = Path(temp_dir) if is_copy else src.parent
            try:
                safe_filename(name)
                if not src.is_file():
                    raise FileNotFoundError(str(src))
            except (ValueError, OSError) as error:
                self._last_error = str(error)
                return None
            dst = target_folder / name

            # 5. 防冲突机制：如果在目标文件夹下已存在同名文件，自动追加编号
            original_dst = dst
            conflict_counter = 1
            while ((dst.exists() or dst.is_symlink()) and dst.resolve() != src.resolve()
                   or str(dst.resolve()).casefold() in reserved):
                dst = target_folder / f"{original_dst.stem}_{conflict_counter}{original_dst.suffix}"
                conflict_counter += 1
            reserved.add(str(dst.resolve()).casefold())
            plan.append((src, dst))

        for src, dst in plan:
            check_cancelled()
            # 6. 最终执行 IO 操作（复制 或 重命名移动）
            # 使用 resolve() 对比，防止覆盖自己，也完美兼容 Windows 大小写不敏感的问题
            if src.resolve() != dst.resolve():
                try:
                    if is_copy:
                        shutil.copy2(str(src), str(dst))
                        # logger.info(f'[{self.NODE_NAME}] 复制到缓存: {src.name} -> {dst.name}')
                    else:
                        shutil.move(str(src), str(dst))
                        # logger.info(f'[{self.NODE_NAME}] 重命名: {src.name} -> {dst.name}')
                except ProcessCancelled:
                    raise
                except Exception as e:
                    action_name = '复制' if is_copy else '重命名'
                    logger.error(f'[{self.NODE_NAME}] {action_name}失败 {src.name}: {e}')
                    self._last_error = QCoreApplication.translate('AMENodes', '文件操作失败: {error}').format(error=e)
                    return None
            
            result.append(str(dst))
            
        return {'file': result}
