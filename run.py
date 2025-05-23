from openai import OpenAI
import json
from tools import all_tools_schemas, available_functions
from config import Config
from utils import extract_json

provider = "gemini"
config = Config()

client = OpenAI(
    api_key=config.get_api_key(provider),
    base_url=config.get_base_url(provider),
)

model = config.get_model(provider)


initial_prompt = """
Write a python code of quick sort in a .py file with several test cases to verify the correctness of the code.
Then run it with command tool, tell me the output.
"""

system_prompt = """
There will be multi-turns of interaction. When you believe the task is complete, include a JSON marker in your response like this:
```json
{"task_complete": true, "message": "Task has been completed successfully"}
```
"""

messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user", 
        "content": initial_prompt
    }
]


def execute_tool_call(tool_call):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    print(f"\nModel requests to call tool:      🛠️ {function_name}")
    print(f"Arguments: {function_args}")
    
    if function_name not in available_functions:
        return json.dumps({"error": f"Unknown function: {function_name}"})

    function_to_call = available_functions[function_name]
    try:
        result = function_to_call(**function_args)
        print(f"\nTool execution result: 📝 {result}\n")
        return result
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        print(error_msg)
        return json.dumps({"error": error_msg})


max_iterations = 5
iteration = 0
task_complete = False


while iteration < max_iterations and not task_complete:
    iteration += 1
    print(f"\n--- Iteration {iteration}/{max_iterations} ---\n")
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=all_tools_schemas,
        tool_choice="auto",
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    json_data = extract_json(response_message.content or "")
    if json_data:
        print("\nTask completion marker detected: 🎉")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        task_complete = True
        continue
    
    tool_calls = response_message.tool_calls
    if tool_calls:
        tool_results = []
        errors = []
        
        for tool_call in tool_calls:
            result = execute_tool_call(tool_call)
            tool_results.append((tool_call.function.name, result))
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": result,
            })
            
            try:
                result_json = json.loads(result)
                if "error" in result_json:
                    errors.append(f"{tool_call.function.name} error: {result_json['error']}")
                elif tool_call.function.name == "execute_shell_command" and result_json.get("returncode", 0) != 0:
                    errors.append(f"Command execution error: {result_json.get('stderr', 'Unknown error')}")
            except json.JSONDecodeError:
                errors.append(f"{tool_call.function.name} error: Could not parse JSON: {result}")
        
        if errors:
            error_feedback = "Errors occurred during execution:\n" + "\n".join(errors) + "\nPlease handle these errors and continue the task."
            print(f"\nErrors:\n{error_feedback}\n")
            
            messages.append({
                "role": "user",
                "content": error_feedback
            })
    else:
        if not task_complete:
            print("Model did not request tool calls, and did not indicate task completion.")
            print("Model's response:")
            print(response_message.content)
            
            feedback = "Please use tools to complete the task, or if the task is complete, please use JSON to indicate completion."
            messages.append({
                "role": "user",
                "content": feedback
            })


if task_complete:
    print("\n=== Task completed successfully! ===\n")
else:
    print("\n=== Reached maximum iteration count, task not explicitly marked as complete ===\n")
