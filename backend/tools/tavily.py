from dotenv import load_dotenv
load_dotenv()
import os

from tavily import TavilyClient


client = TavilyClient()

def tavily_search(query: str):

    return client.search(
        api_key=os.getenv("TAVILY_API_KEY"),
        query=query,
        max_results=2,
        include_raw_content=False,
    )