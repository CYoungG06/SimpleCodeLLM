import requests
from config import Config
from .decorator import tool

config = Config()

@tool()
def web_search(
    query: str,
    topic: str = "general",
    search_depth: str = "basic",
    max_results: int = 5,
) -> str:
    """
    Search the web for a query and return the results using Tavily API.
    
    Args:
        query: The search query
        topic: The topic of the search (default: "general")
        search_depth: Depth of search - "basic" or "advanced" (default: "basic")
        max_results: Maximum number of results to return (default: 5)
    
    Return template (type: str):
        {
            "query": "",
            "answer": "",
            "images": [],
            "results": [
                {
                "title": "",
                "url": "",
                "content": "",
                "score": ...,
                "raw_content": ""
                }
            ],
            "response_time": ""
            }
    """
    url = "https://api.tavily.com/search"
    
    payload = {
        "query": query,
        "topic": topic,
        "search_depth": search_depth,
        "max_results": max_results,
    }
    
    headers = {
        "Authorization": f"Bearer {config.get_search_key()}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error {response.status_code}: {response.text}"
        print(f"Tavily API Error: {error_msg}")
        return f'{{"error": "Search API error: {error_msg}"}}'
    except Exception as e:
        error_msg = f"Search request failed: {str(e)}"
        print(f"Search Error: {error_msg}")
        return f'{{"error": "{error_msg}"}}'
