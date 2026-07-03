from dotenv import load_dotenv
load_dotenv()
import os

from tavily import TavilyClient


client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search(query: str) -> dict:
    return client.search(
        query=query,
        max_results=2,
        include_raw_content=False,
    )