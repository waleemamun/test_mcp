import arxiv
import json
import os
import ssl
import certifi
import urllib3
import requests
from urllib3.util.ssl_ import create_urllib3_context
from typing import List
from mcp.server.fastmcp import FastMCP

# Disable SSL warnings for arXiv SSL issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set SSL environment variables
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Configure requests session with custom SSL settings
session = requests.Session()
session.verify = certifi.where()

# Configure urllib3 SSL context
ctx = create_urllib3_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    print(f"Searching for papers on topic: {topic} with max results: {max_results}")
    try:
        # Try to use requests to test the connection first
        print("Testing connection to arXiv...")
        test_url = "https://export.arxiv.org/api/query?search_query=test&max_results=1"
        
        try:
            response = session.get(test_url, timeout=10)
            print(f"Connection test successful: {response.status_code}")
        except Exception as conn_e:
            print(f"Connection test failed: {conn_e}")
            # Fall back to insecure connection
            session.verify = False
        
        # Configure SSL context to handle SSL issues on macOS
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Use arxiv to find the papers with custom configuration
        client = arxiv.Client(
            page_size=max_results,
            delay_seconds=3.0,  # Increase delay to be more respectful
            num_retries=3       # Reduce retries to fail faster
        )

        # Search for the most relevant articles matching the queried topic
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        # Convert to list to handle the generator and potential SSL timeouts
        print(f"Searching for papers on topic: {topic}")
        papers_list = list(client.results(search))
        print(f"Found {len(papers_list)} papers")
        
        # Create directory for this topic
        path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
        os.makedirs(path, exist_ok=True)
        
        file_path = os.path.join(path, "papers_info.json")

        # Try to load existing papers info
        try:
            with open(file_path, "r") as json_file:
                papers_info = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            papers_info = {}

        # Process each paper and add to papers_info  
        paper_ids = []
        for paper in papers_list:
            paper_ids.append(paper.get_short_id())
            paper_info = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'summary': paper.summary,
                'pdf_url': paper.pdf_url,
                'published': str(paper.published.date())
            }
            papers_info[paper.get_short_id()] = paper_info
        
        # Save updated papers_info to json file
        with open(file_path, "w") as json_file:
            json.dump(papers_info, json_file, indent=2)
        
        print(f"Results are saved in: {file_path}")
        
        return paper_ids
        
    except Exception as e:
        error_msg = f"Error searching papers: {str(e)}"
        print(error_msg)
        return [error_msg]

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."
@mcp.tool()
def download_paper_pdf(paper_id: str, filename: str = None) -> bool:
        """
        Download PDF of a paper
        
        Args:
            paper_id: arXiv paper ID
            filename: Optional filename for the PDF
        
        Returns:
            True if successful, False otherwise
        """
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        
        if not filename:
            filename = f"arxiv_{paper_id}.pdf"
        
        # Ensure the PAPER_DIR exists
        os.makedirs(PAPER_DIR, exist_ok=True)
        
        # Create full file path under PAPER_DIR
        full_file_path = os.path.join(PAPER_DIR, filename)
        
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            with open(full_file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {full_file_path}")
            return True
            
        except requests.RequestException as e:
            print(f"Error downloading PDF: {e}")
            return False



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
