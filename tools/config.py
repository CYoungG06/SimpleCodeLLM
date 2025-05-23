import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")

def get_workspace_path(relative_path=None):
    if relative_path is None:
        return WORKSPACE_DIR
    
    normalized_path = os.path.normpath(relative_path)
    
    if os.path.isabs(normalized_path) and normalized_path.startswith(WORKSPACE_DIR):
        return normalized_path
    
    return os.path.join(WORKSPACE_DIR, normalized_path)

def is_path_in_workspace(path):
    abs_path = os.path.abspath(path)
    return abs_path.startswith(WORKSPACE_DIR)
