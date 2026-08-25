import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information not available in the knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
            },
            "required": ["query"],
        },
    },
}


def web_search(query: str) -> str:
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(query=query, search_depth="advanced")
    results = response.get("results", [])
    if not results:
        return "No results found."
    return "\n\n".join(
        f"{r['title']}\n{r['url']}\n{r['content']}" for r in results
    )
