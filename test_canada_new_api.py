from dotenv import load_dotenv
import os
import json
from typing import List
import requests

load_dotenv()

def test_canada_new_api(topic:str):
    """
    Test the new Canada API for a given topic.
    
    Args:
        topic: The topic to search for in the Canada API.
        
    Returns:
        A list of paper IDs related to the topic.
    """
    everything_url = 'https://newsapi.org/v2/everything?'+ 'q=' + topic +'&sortBy=popularity' +'' +'&apiKey=' + os.getenv('CANADA_NEWS_API_KEY')
    url = everything_url
    latest_url = 'https://newsapi.org/v2/top-headlines?country=us&apiKey=' + os.getenv('CANADA_NEWS_API_KEY')
    if topic.lower() == 'latest':
        url = latest_url
    else:
        url = everything_url
    print(f"Testing Canada API with URL: {url}")  # Debugging line

    
    
    try:
        response = requests.get(url)
    
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        total_results = data.get('totalResults', 0)
        print(f"Total results found: {total_results}")  # Debugging line
        # get top 5 papers articles
        top_five_articles = data.get('articles', [])[:5]
        article_list = {}
        for article in top_five_articles:
            print(f"Article title: {article.get('title', 'No title')}, URL: {article.get('url', 'No URL')}")
            article_list[article.get('title', 'No title')] = article.get('url', 'No URL')

        if 'papers' in data:
            paper_ids = [paper['id'] for paper in data['papers']]
            return paper_ids
        else:
            return ["No papers found for this topic."]
    
    except requests.RequestException as e:
        return [f"Error fetching data from Canada API: {str(e)}"]
    
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
    # topic = "latest"
    # result = test_canada_new_api(topic)
    # print(f"Result for topic '{topic}': {result}")
    title_dict = search_news("Canada", 5)
    for title, url in title_dict.items():
        print(f"Title: {title}, URL: {url}")

