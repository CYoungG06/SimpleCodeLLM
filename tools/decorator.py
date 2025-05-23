import functools
import inspect
import asyncio
from typing import Dict, List, Any, Callable, Optional, get_type_hints

registered_tools = {}
tool_schemas = []
async_tools = set()  # Track which tools are async

def tool(name: Optional[str] = None, description: Optional[str] = None):
    def decorator(func: Callable):
        func_name = name or func.__name__
        func_description = description or inspect.getdoc(func) or ""
        
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        properties = {}
        required = []
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = type_hints.get(param_name, Any).__name__
            param_doc = _extract_param_doc(func_description, param_name)
            
            properties[param_name] = {
                "type": _python_type_to_json_type(param_type),
                "description": param_doc
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
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
        
        registered_tools[func_name] = func
        tool_schemas.append(tool_schema)
        
        # Check if the function is async and track it
        if inspect.iscoroutinefunction(func):
            async_tools.add(func_name)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def _extract_param_doc(docstring: str, param_name: str) -> str:
    if not docstring:
        return ""
    
    lines = docstring.split("\n")
    param_marker = f"{param_name} "
    param_marker_with_type = f"{param_name} ("
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith(param_marker) or line.startswith(param_marker_with_type):
            description = line.split(":", 1)[1].strip() if ":" in line else ""
            
            j = i + 1
            while j < len(lines) and lines[j].strip() and not any(lines[j].strip().startswith(p) for p in ["Args:", "Returns:", "Raises:", "Yields:", "Example:", "Note:"]):
                description += " " + lines[j].strip()
                j += 1
                
            return description
    
    return ""

def _python_type_to_json_type(type_name: str) -> str:
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
    return registered_tools

def get_tool_schemas() -> List[Dict[str, Any]]:
    return tool_schemas

def get_async_tools() -> set:
    return async_tools
