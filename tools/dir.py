import os
import json
from .config import get_workspace_path, is_path_in_workspace
from .decorator import tool

@tool()
def list_directory_contents(directory_path: str) -> str:
    """
    List the contents of a directory.

    Args:
        directory_path: The path to the directory to list. Can be a relative path from the workspace 
                       directory (e.g., "subfolder") or an absolute path within the workspace directory.

    Returns:
        A JSON string containing the directory contents with file and directory information.
    """
    try:
        # Convert to absolute path within workspace
        abs_directory_path = get_workspace_path(directory_path)
        
        # For security reasons, we limit the directory path to the workspace directory
        if not is_path_in_workspace(abs_directory_path):
            return json.dumps({"error": "Access to the directory is not allowed."})
        
        if not os.path.exists(abs_directory_path):
            return json.dumps({"error": f"Directory '{abs_directory_path}' does not exist."})
        if not os.path.isdir(abs_directory_path):
            return json.dumps({"error": f"Path '{abs_directory_path}' is not a directory."})

        contents = os.listdir(abs_directory_path)
        items = []
        for item in contents:
            item_path = os.path.join(abs_directory_path, item)
            item_type = "file" if os.path.isfile(item_path) else "directory" if os.path.isdir(item_path) else "unknown"
            items.append({"name": item, "type": item_type})

        return json.dumps({"success": True, "directory_path": abs_directory_path, "contents": items})
    except Exception as e:
        return json.dumps({"error": f"List '{abs_directory_path}' failed: {str(e)}"})
