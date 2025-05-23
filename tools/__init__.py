# 导入装饰器系统
from .decorator import get_registered_tools, get_tool_schemas

# 导入所有工具模块，确保装饰器被执行
from .file import *
from .command import *
from .dir import *
from .execute import *

# 获取注册的工具和工具模式
available_functions = get_registered_tools()
all_tools_schemas = get_tool_schemas()

__all__ = [
    'available_functions',
    'all_tools_schemas',
] + list(available_functions.keys())