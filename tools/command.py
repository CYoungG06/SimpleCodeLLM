import subprocess
import json
import os
from .config import get_workspace_path
from .decorator import tool

@tool()
def execute_shell_command(command: str) -> str:
    """
    Executes a shell command and returns the output as a JSON string.
    Commands are executed in the workspace directory.

    Args:
        command: The shell command to execute.

    Returns:
        A JSON string containing the command output with stdout, stderr, and returncode.
    """
    try:
        # allowed_commands = ["ls", "echo", "mkdir", "cat", "python"] # Whitelist of allowed commands
        # if not any(command.startswith(allowed_cmd) for allowed_cmd in allowed_commands):
        #     return json.dumps({"error": "Command not allowed"})
        workspace_dir = get_workspace_path()
        os.makedirs(workspace_dir, exist_ok=True)
            
        process = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30,
            cwd=workspace_dir
        )
        
        return json.dumps({
            "success": True,
            "command": command,
            "returncode": process.returncode,
            "workspace_dir": workspace_dir,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip()
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Executing command '{command}' timed out."})
    except Exception as e:
        return json.dumps({"error": f"Executing command '{command}' failed: {str(e)}"})