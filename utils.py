import re
import json






def extract_json(content):
    pattern = r'```json\s*({.*?})\s*```'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        try:
            completion_data = json.loads(match.group(1))
            if isinstance(completion_data, dict) and completion_data.get("task_complete") is True:
                return completion_data
        except json.JSONDecodeError:
            pass
    return None