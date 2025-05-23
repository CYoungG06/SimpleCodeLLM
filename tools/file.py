import os
import json
from .config import get_workspace_path, is_path_in_workspace
from .decorator import tool

@tool()
def read_file(file_path: str) -> str:
    """
    Read the content of a file.

    Args:
        file_path: The path of the file to read. Can be a relative path from the workspace directory 
                  (e.g., "file.txt") or an absolute path within the workspace directory.

    Returns:
        A JSON string containing the file content or an error message.
    """
    try:
        # Convert to absolute path within workspace
        abs_file_path = get_workspace_path(file_path)
        
        # For security reasons, we limit the file path to the workspace directory
        if not is_path_in_workspace(abs_file_path):
            return json.dumps({"error": "File access out of allowed range"})
        if not os.path.exists(abs_file_path):
            return json.dumps({"error": f"File '{abs_file_path}' does not exist"})
        if not os.path.isfile(abs_file_path):
            return json.dumps({"error": f"Path '{abs_file_path}' is not a file"})

        with open(abs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"success": True, "file_path": abs_file_path, "content": content})
    except Exception as e:
        return json.dumps({"error": f"Reading file '{abs_file_path}' failed: {str(e)}"})

@tool()
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        file_path: The path of the file to write. Can be a relative path from the workspace directory 
                  (e.g., "file.txt") or an absolute path within the workspace directory.
        content: The content to write to the file.

    Returns:
        A JSON string indicating the success or failure of the operation.
    """
    try:
        # Convert to absolute path within workspace
        abs_file_path = get_workspace_path(file_path)
        
        # For security reasons, we limit the file path to the workspace directory
        if not is_path_in_workspace(abs_file_path):
            return json.dumps({"error": "File access out of allowed range"})

        directory = os.path.dirname(abs_file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(abs_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"success": True, "file_path": abs_file_path, "message": "File written successfully"})
    except Exception as e:
        return json.dumps({"error": f"Writing file '{abs_file_path}' failed: {str(e)}"})

