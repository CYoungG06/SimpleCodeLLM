import json
import os
import traceback
import asyncio
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent
from browser_use.agent.views import AgentHistoryList
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from langchain_openai import ChatOpenAI
from pydantic import Field
from .decorator import tool
from config import Config

provider = "gemini"
config = Config()
api_key = config.get_api_key(provider)
base_url = config.get_base_url(provider)
model = config.get_model(provider)


browser_system_prompt = """
===== NAVIGATION STRATEGY =====
1. START: Navigate to the most authoritative source for this information
   - For general queries: Use Google with specific search terms
   - For known sources: Go directly to the relevant website

2. EVALUATE: Assess each page methodically
   - Scan headings and highlighted text first
   - Look for data tables, charts, or official statistics
   - Check publication dates for timeliness

3. EXTRACT: Capture exactly what's needed
   - Take screenshots of visual evidence (charts, tables, etc.)
   - Copy precise text that answers the query
   - Note source URLs for citation

4. DOWNLOAD: Save the most relevant file to local path for further processing
   - Save the text if possible for futher text reading and analysis
   - Save the image if possible for futher image reasoning analysis
   - Save the pdf if possible for futher pdf reading and analysis

5. ROBOT DETECTION:
   - If the page is a robot detection page, abort immediately
   - Navigate to the most authoritative source for similar information instead

===== EFFICIENCY GUIDELINES =====
- Use specific search queries with key terms from the task
- Avoid getting distracted by tangential information
- If blocked by paywalls, try archive.org or similar alternatives
- Document each significant finding clearly and concisely

Your goal is to extract precisely the information needed with minimal browsing steps.
"""


@tool()
async def browser_use(
    task: str = Field(description="The task to perform using the browser."),
) -> str:
    """
    Perform browser actions using the browser-use package.
    Args:
        task (str): The task to perform using the browser.
    Returns:
        str: The result of the browser actions.
    """
    browser = Browser(
        config=BrowserConfig(
            headless=False,
            new_context_config=BrowserContextConfig(
                disable_security=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                minimum_wait_page_load_time=10,
                maximum_wait_page_load_time=30,
            ),
        )
    )
    browser_context = BrowserContext(
        config=BrowserContextConfig(
            trace_path="./browser_trace",
        ),
        browser=browser,
    )
    import os
    os.environ["OPENAI_API_KEY"] = api_key
    
    agent = Agent(
        task=task,
        llm=ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
        ),
        browser_context=browser_context,
        extend_system_message=browser_system_prompt,
    )
    try:
        browser_execution: AgentHistoryList = await agent.run(max_steps=50)
        if (
            browser_execution is not None
            and browser_execution.is_done()
            and browser_execution.is_successful()
        ):
            exec_trace = browser_execution.extracted_content()
            print(
                ">>> 🌏 Browse Execution Succeed!\n"
                f">>> 💡 Result: {json.dumps(exec_trace, ensure_ascii=False, indent=4)}\n"
                ">>> 🌏 Browse Execution Succeed!\n"
            )
            result = browser_execution.final_result()
            return json.dumps({"success": True, "result": result})
        else:
            return json.dumps({"error": f"Browser execution failed for task: {task}"})
    except Exception as e:
        print(f"Browser execution failed: {traceback.format_exc()}")
        return json.dumps({"error": f"Browser execution failed for task: {task} due to {str(e)}"})
    finally:
        try:
            # Close browser context first, then browser
            if 'browser_context' in locals() and browser_context:
                try:
                    await browser_context.close()
                except Exception:
                    pass  # Ignore context close errors
            
            if 'browser' in locals() and browser:
                try:
                    await browser.close()
                except Exception:
                    pass  # Ignore browser close errors
            
            # Use a small delay to allow cleanup
            import asyncio
            import gc
            
            try:
                await asyncio.sleep(0.1)  # Use async sleep instead of time.sleep
            except:
                pass
            
            gc.collect()
            print("Browser resources cleaned up")
            
            # Clear references
            if 'browser' in locals():
                browser = None
            if 'browser_context' in locals():
                browser_context = None
            gc.collect()
        except Exception as e:
            print(f"Error during browser cleanup: {e}")
            try:
                import gc
                gc.collect()
                print("Forced final cleanup")
            except:
                pass
