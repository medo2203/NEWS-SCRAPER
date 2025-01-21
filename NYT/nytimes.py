import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
import urllib.request
import datetime
import random
import time
import json

# Current date for logging and file naming
date = datetime.datetime.now()
curr_date = f"{date.day}/{date.month}/{date.year}"

# NYT RSS feed sections
NYT_ARTICLE_URLS = (
    'world', 'us', 'politics', 'nyregion', 'business', 'technology',
    'science', 'health', 'sports', 'arts', 'books', 'movies',
    'theater', 'fashion', 'food', 'travel', 'magazine', 'opinion'
)

def fetch_rss_feed(url):
    """Fetches and parses an RSS feed from a URL."""
    try:
        return ET.parse(source=urllib.request.urlopen(url))
    except (HTTPError, URLError) as err:
        print(f"Network error while fetching {url}: {err}")
    except ET.ParseError as err:
        print(f"Error parsing XML from {url}: {err}")
    return None

def get_nyt_articles(section):
    """Fetches and parses articles from NYT RSS feeds."""
    url = f'https://rss.nytimes.com/services/xml/rss/nyt/{section}.xml'
    
    tree = fetch_rss_feed(url)
    if not tree:
        return None
        
    root = tree.getroot()
    articles = []
    
    for item in root.findall('.//item'):
        # Extract title
        title = item.find('title').text if item.find('title') is not None else "No title"
        
        # Extract description/summary
        description = item.find('description')
        subline = description.text if description is not None else "No description"
        
        # Extract media (if available)
        media_content = item.find('.//{http://search.yahoo.com/mrss/}content[@medium="image"]')
        image = media_content.get('url') if media_content is not None else None
        
        # Create article object
        articles.append({
            "title": title,
            "image": image,
            "subline": subline
        })
    
    return articles

def write_json(data, filename):
    """Writes data to a JSON file."""
    try:
        with open(filename, 'a', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.write(",\n")
    except IOError as err:
        print(f"Error writing to file {filename}: {err}")

def scrape_nyt(section):
    """Scrapes articles for a given NYT section."""
    articles = get_nyt_articles(section)
    if articles:
        data = {
            "date": curr_date,
            "website": "NYT",
            "section": section,
            "articles": articles
        }
        write_json(data, 'NYT_articles.json')
        print(f"Downloaded articles from NYT section: {section}")
    else:
        error_data = {
            "date": curr_date,
            "website": "NYT",
            "section": section,
            "error": "Failed to download articles"
        }
        write_json(error_data, 'errorLog.json')
        print(f"Failed to download articles from NYT section: {section}")

def main():
    """Main function to start NYT scraping."""
    print("Starting New York Times RSS feed scraper...")
    
    for section in NYT_ARTICLE_URLS:
        scrape_nyt(section)
        # Random delay between requests to avoid overwhelming the server
        time.sleep(random.uniform(1, 2))
    
    print("NYT scraping completed!")

if __name__ == '__main__':
    main()