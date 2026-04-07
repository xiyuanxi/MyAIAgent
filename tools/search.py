from langchain_tavily import TavilySearch


def create_tavily_search():
    return TavilySearch(max_results=3)
