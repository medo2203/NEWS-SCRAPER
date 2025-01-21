import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
import urllib.request
import datetime
import random
import time
import json
import ssl
import re

# Current date for logging and file naming
date = datetime.datetime.now()
curr_date = f"{date.day}/{date.month}/{date.year}"

# NPR RSS feed sections with their URLs
NPR_ARTICLE_URLS = {
    'news': 'https://feeds.npr.org/1001/rss.xml',
    'world': 'https://feeds.npr.org/1004/rss.xml',
    'politics': 'https://feeds.npr.org/1014/rss.xml',
    'business': 'https://feeds.npr.org/1006/rss.xml',
    'technology': 'https://feeds.npr.org/1019/rss.xml',
    'science': 'https://feeds.npr.org/1007/rss.xml',
    'health': 'https://feeds.npr.org/1128/rss.xml',
    'arts': 'https://feeds.npr.org/1008/rss.xml',
    'books': 'https://feeds.npr.org/1032/rss.xml',
    'music': 'https://feeds.npr.org/1039/rss.xml',
    'movies': 'https://feeds.npr.org/1045/rss.xml',
    'sports': 'https://feeds.npr.org/1055/rss.xml',
}

def create_ssl_context():
    """Creates an SSL context that ignores certificate verification."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

def fetch_rss_feed(url):
    """Fetches and parses an RSS feed from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        context = create_ssl_context()
        response = urllib.request.urlopen(request, context=context)
        return ET.parse(source=response)
    except (HTTPError, URLError) as err:
        print(f"Network error while fetching {url}: {err}")
    except ET.ParseError as err:
        print(f"Error parsing XML from {url}: {err}")
    return None

def extract_image_from_content(content):
    """Extracts image information from content:encoded CDATA section."""
    if not content:
        return None
    
    # Extract image URL
    img_match = re.search(r"<img src='([^']+)'", content)
    if not img_match:
        return None
    
    image_url = img_match.group(1)
    
    # Extract alt text if available
    alt_match = re.search(r"alt='([^']+)'", content)
    alt_text = alt_match.group(1) if alt_match else None
    
    # Extract image credit if available
    credit_match = re.search(r"\(Image credit: ([^)]+)\)", content)
    credit = credit_match.group(1) if credit_match else None
    
    # Filter out tracking pixel
    if 'tracking' in image_url or 'npr-rss-pixel' in image_url:
        return None
        
    return {
        'url': image_url,
        'alt_text': alt_text,
        'credit': credit,
        'type': 'main_image'
    }

def get_npr_articles(section, url):
    """Fetches and parses articles from NPR RSS feeds."""
    tree = fetch_rss_feed(url)
    if not tree:
        return None
        
    root = tree.getroot()
    channel = root.find('channel')
    if channel is None:
        return None
    
    articles = []
    
    for item in channel.findall('item'):
        # Extract basic metadata
        title = item.find('title')
        title = title.text if title is not None else "No title"
        
        link = item.find('link')
        link = link.text if link is not None else None
        
        description = item.find('description')
        description = description.text if description is not None else "No description"
        
        pub_date = item.find('pubDate')
        pub_date = pub_date.text if pub_date is not None else None
        
        # Extract author/creator
        author = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
        author = author.text if author is not None else None
        
        # Extract GUID
        guid = item.find('guid')
        guid = guid.text if guid is not None else None
        
        # Extract content:encoded for images
        content = item.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
        content_text = content.text if content is not None else None
        
        # Extract image from content:encoded
        image_data = extract_image_from_content(content_text)
        images = [image_data] if image_data else []
        
        # Create article object
        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "author": author,
            "guid": guid,
            "images": images
        }
        
        articles.append(article)
    
    return articles

def write_json(data, filename):
    """Writes data to a JSON file."""
    try:
        with open(filename, 'a', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.write(",\n")
    except IOError as err:
        print(f"Error writing to file {filename}: {err}")

def scrape_npr(section, url):
    """Scrapes articles for a given NPR section."""
    articles = get_npr_articles(section, url)
    if articles:
        data = {
            "date": curr_date,
            "website": "NPR",
            "section": section,
            "articles": articles
        }
        write_json(data, 'NPR_articles.json')
        print(f"Downloaded articles from NPR section: {section}")
    else:
        error_data = {
            "date": curr_date,
            "website": "NPR",
            "section": section,
            "error": "Failed to download articles"
        }
        write_json(error_data, 'errorLog.json')
        print(f"Failed to download articles from NPR section: {section}")

def main():
    """Main function to start NPR scraping."""
    print("Starting NPR RSS feed scraper...")
    
    for section, url in NPR_ARTICLE_URLS.items():
        scrape_npr(section, url)
        # Random delay between requests to avoid overwhelming the server
        time.sleep(random.uniform(1.5, 3))
    
    print("NPR scraping completed!")

if __name__ == '__main__':
    main()