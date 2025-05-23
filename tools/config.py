import os

# Get the project root directory (the directory containing the 'tools' and 'workspace' directories)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the workspace directory relative to the project root
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")

def get_workspace_path(relative_path=None):
    """
    Get the absolute path to the workspace directory or a file within it.
    
    Args:
        relative_path (str, optional): A path relative to the workspace directory.
            If None, returns the workspace directory path.
    
    Returns:
        str: The absolute path to the workspace directory or the specified file within it.
    """
    if relative_path is None:
        return WORKSPACE_DIR
    
    # Normalize the path to handle cases like "../file.txt" or "./file.txt"
    normalized_path = os.path.normpath(relative_path)
    
    # If the path is already absolute and within the workspace, return it
    if os.path.isabs(normalized_path) and normalized_path.startswith(WORKSPACE_DIR):
        return normalized_path
    
    # Otherwise, join it with the workspace directory
    return os.path.join(WORKSPACE_DIR, normalized_path)

def is_path_in_workspace(path):
    """
    Check if a path is within the workspace directory.
    
    Args:
        path (str): The path to check.
    
    Returns:
        bool: True if the path is within the workspace directory, False otherwise.
    """
    abs_path = os.path.abspath(path)
    return abs_path.startswith(WORKSPACE_DIR)
