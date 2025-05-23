import functools
import inspect
from typing import Dict, List, Any, Callable, Optional, get_type_hints

# 存储所有注册的工具
registered_tools = {}
tool_schemas = []

def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    装饰器，用于注册工具函数并自动生成工具的schema
    
    Args:
        name: 工具名称，如果不提供则使用函数名
        description: 工具描述，如果不提供则使用函数的文档字符串
    
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable):
        # 获取函数名称和描述
        func_name = name or func.__name__
        func_description = description or inspect.getdoc(func) or ""
        
        # 获取函数参数信息
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # 构建参数schema
        properties = {}
        required = []
        
        for param_name, param in signature.parameters.items():
            # 跳过self参数
            if param_name == 'self':
                continue
                
            param_type = type_hints.get(param_name, Any).__name__
            param_doc = _extract_param_doc(func_description, param_name)
            
            properties[param_name] = {
                "type": _python_type_to_json_type(param_type),
                "description": param_doc
            }
            
            # 如果参数没有默认值，则为必需参数
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        # 构建工具schema
        tool_schema = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": func_description.split("\n\n")[0].strip(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        
        # 注册工具
        registered_tools[func_name] = func
        tool_schemas.append(tool_schema)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def _extract_param_doc(docstring: str, param_name: str) -> str:
    """从函数文档字符串中提取参数的描述"""
    if not docstring:
        return ""
    
    lines = docstring.split("\n")
    param_marker = f"{param_name} "
    param_marker_with_type = f"{param_name} ("
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith(param_marker) or line.startswith(param_marker_with_type):
            # 找到参数描述的起始行
            description = line.split(":", 1)[1].strip() if ":" in line else ""
            
            # 检查下一行是否为参数描述的延续
            j = i + 1
            while j < len(lines) and lines[j].strip() and not any(lines[j].strip().startswith(p) for p in ["Args:", "Returns:", "Raises:", "Yields:", "Example:", "Note:"]):
                description += " " + lines[j].strip()
                j += 1
                
            return description
    
    return ""

def _python_type_to_json_type(type_name: str) -> str:
    """将Python类型名称转换为JSON schema类型"""
    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
        "None": "null"
    }
    return type_map.get(type_name, "string")

def get_registered_tools() -> Dict[str, Callable]:
    """获取所有注册的工具函数"""
    return registered_tools

def get_tool_schemas() -> List[Dict[str, Any]]:
    """获取所有工具的schema"""
    return tool_schemas
