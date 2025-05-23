import json
import sys
import re
import asyncio
from openai import OpenAI
from tools import all_tools_schemas, available_functions, get_async_tools
from config import Config
from utils import extract_json
from logger import MessageLogger
from time import time

current_time = time()

provider = "gemini"
config = Config()

client = OpenAI(
    api_key=config.get_api_key(provider),
    base_url=config.get_base_url(provider),
)

model = config.get_model(provider)

# Initialize message logger
logger = MessageLogger(config)

user_prompt = """
Go to huggingface.co to search qwen3 model series and make a brief summary.
"""

# user_prompt = "What integer-rounded percentage of the total length of the harlequin shrimp recorded in Omar Valencfia-Mendez 2017 paper was the sea star fed to the same type of shrimp in G. Curt Fiedler's 2002 paper?"

# user_prompt = """
# What tools do you have?
# """

# user_prompt = "Search for some papers about LLM / Agent / RL recently (about May 2025) published on arxiv. Then find the main points of the papers through their abstracts. Finally summarize them with the style of the red note (xiaohongshu)."

system_prompt = """
Current time: {current_time}
---
You are a helpful assistant, and you have access to a set of tools. Your task is to try your best to complete the user's request.
What you should do FIRST is to make a high-level plan for the task to instruct your following actions, but it's totally OK that you can adjust it during the process of the task, finally make sure you have completed the task.

For completing the task, there will be multiple turns of interaction with tool invoking, observation and reasoning for each turn. And only when you believe the task is complete, include a JSON marker within the ```json block in your response like this:
```json
{"task_complete": true, "message": "The answer or summary of the task"}
```
For the task that requires a certain answer, you should finally give the answer in the "message" field above.
For the task that requires non-specific answer but requires open-ended text generating, you should finally give the generated text according to the user's request and the additional information you have learned from the tools in the "message" field above.
"""

messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user", 
        "content": f"**User request**: {user_prompt}"
    }
]

# Log session start
logger.log_session_start(user_prompt, system_prompt, provider, model)
print(f"📝 Session started with ID: {logger.get_session_id()}")


async def execute_tool_call(tool_call):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    print(f"\nModel requests to call tool:      🛠️ {function_name}\n")
    print(f"Arguments: {function_args}")
    
    if function_name not in available_functions:
        return json.dumps({"error": f"Unknown function: {function_name}"})

    function_to_call = available_functions[function_name]
    async_tools = get_async_tools()
    
    try:
        if function_name in async_tools:
            # This is an async function, await it
            result = await function_to_call(**function_args)
        else:
            # This is a sync function, call it normally
            result = function_to_call(**function_args)
        
        print(f"\nTool execution result: 📝 {result}\n")
        
        # Log tool call and result
        logger.log_tool_call(function_name, function_args, result)
        
        return result
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        print(error_msg)
        return json.dumps({"error": error_msg})


max_iterations = 16
iteration = 0
task_complete = False
task_message = ""


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
    
    # Log the model response
    logger.log_message({
        "role": response_message.role,
        "content": response_message.content,
        "tool_calls": [{"function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in (response_message.tool_calls or [])]
    }, "model_response")
    
    json_data = extract_json(response_message.content or "")
    if json_data:
        print("\nTask completion marker detected: 🎉")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
    
    # 检查是否包含任务完成标记
    if response_message.content:
        # 使用正则表达式匹配JSON标记
        json_pattern = r'```json\s*({[\s\S]*?})\s*```'
        json_matches = re.findall(json_pattern, response_message.content)
        
        for json_str in json_matches:
            try:
                json_data = json.loads(json_str)
                if json_data.get('task_complete') == True:
                    task_complete = True
                    task_message = json_data.get('message', "Task completed without specific message")
                    break
            except json.JSONDecodeError:
                pass
    
    tool_calls = response_message.tool_calls
    if tool_calls:
        async def process_tool_calls():
            tool_results = []
            errors = []
            
            for tool_call in tool_calls:
                result = await execute_tool_call(tool_call)
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
            
            return errors
        
        # Execute the async tool calls
        errors = asyncio.run(process_tool_calls())
        
        if errors:
            error_feedback = "Errors occurred during execution:\n" + "\n".join(errors) + "\nPlease handle these errors and continue the task."
            print(f"\nErrors:\n{error_feedback}\n")
            
            messages.append({
                "role": "user",
                "content": error_feedback
            })
            
            # Log error feedback
            logger.log_message({
                "role": "user",
                "content": error_feedback
            }, "error_feedback")
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
            
            # Log feedback message
            logger.log_message({
                "role": "user",
                "content": feedback
            }, "system_feedback")


# Log session end
logger.log_session_end(task_complete, task_message, iteration)

if task_complete:
    print("\n=== Task completed successfully! ===\n")
    print(f"Final answer: {task_message}\n")
    # 任务成功完成，返回结果
    sys.exit(0)
else:
    print("\n=== Reached maximum iteration count, task not explicitly marked as complete ===\n")
    # 任务未能在最大迭代次数内完成
    sys.exit(1)
