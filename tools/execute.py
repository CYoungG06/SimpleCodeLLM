import io
import json
from contextlib import redirect_stdout
from .decorator import tool

@tool()
def execute_python_code(code: str) -> str:
    """
    Executes Python code and captures the output.

    Args:
        code: The Python code to execute as a string.

    Returns:
        A JSON string containing the execution results, including stdout and any errors.
    """
    # 安全性考虑：这只是一个非常基础的实现。
    # 生产环境需要更复杂的沙箱机制，例如使用 RestrictedPython、pysandbox，
    # 或者在 Docker 容器等隔离环境中执行。
    # 限制可用的内建函数和模块。
    # 创建一个单一的命名空间，同时用于全局和局部变量
    namespace = {
        '__builtins__': {
            'print': print,
            'len': len,
            'range': range,
            'list': list,
            'dict': dict,
            'str': str,
            'int': int,
            'float': float,
            'True': True,
            'False': False,
            'None': None,
            'json': json,
            'sorted': sorted
            # 在此添加其他允许的内建函数或模块
        },
        'json': json # 使 json 模块在代码中可用
    }
    # 简单的输出捕获
    stdout_capture = io.StringIO()
    try:
        with redirect_stdout(stdout_capture):
            exec(code, namespace, namespace)  # 使用同一个字典作为globals和locals
        output = stdout_capture.getvalue()
        # 你可能还想捕获最后一个表达式的值，但这会更复杂
        return json.dumps({"success": True, "code": code, "stdout": output.strip(), "returned_value": None}) # 简单起见，不捕获返回值
    except Exception as e:
        return json.dumps({"error": f"Execution failed: {type(e).__name__}: {str(e)}", "stdout": stdout_capture.getvalue().strip()})
    finally:
        stdout_capture.close()
