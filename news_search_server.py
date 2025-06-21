from dotenv import load_dotenv
import os
import json
import requests
from typing import List
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("news_search")
@mcp.tool()
def search_news(query: str, max_results: int = 5) -> dict:
    """
    Search for news articles based on a query and return their titles.
    
    Args:
        query: The search query
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of article titles found in the search
    """
    print(f"Searching for news articles with query: {query} and max results: {max_results}")
    
    # Example API endpoint (replace with actual news API)
    api_url = "https://newsapi.org/v2/everything"
    api_key = os.getenv("CANADA_NEWS_API_KEY")
    
    params = {
        "q": query,
        "pageSize": max_results,
        "apiKey": api_key
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        
        articles = response.json().get("articles", [])

        news_dict= {}
        for article in articles:
            title = article.get("title", "No title")
            url = article.get("url", "No URL")
            news_dict[title] = url
        print(f"Found {len(news_dict)} articles")
        return news_dict
    
    
    except requests.RequestException as e:
        print(f"Error fetching news articles: {e}")
        return []

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')