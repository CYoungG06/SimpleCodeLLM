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
            'sorted': sorted,
            '__import__': __import__,
        },
        'json': json
    }
    stdout_capture = io.StringIO()
    try:
        with redirect_stdout(stdout_capture):
            exec(code, namespace, namespace)
        output = stdout_capture.getvalue()
        return json.dumps({"success": True, "code": code, "stdout": output.strip(), "returned_value": None})
    except Exception as e:
        return json.dumps({"error": f"Execution failed: {type(e).__name__}: {str(e)}", "stdout": stdout_capture.getvalue().strip()})
    finally:
        stdout_capture.close()
