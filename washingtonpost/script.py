import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
import urllib.request
import datetime
import random
import time
import json
import ssl

# Current date for logging and file naming
date = datetime.datetime.now()
curr_date = f"{date.day}/{date.month}/{date.year}"

# Washington Post RSS feed sections with correct URLs
WAPO_ARTICLE_URLS = {
    'politics': 'https://feeds.washingtonpost.com/rss/politics',
    'opinions': 'https://feeds.washingtonpost.com/rss/opinions',
    'local': 'https://feeds.washingtonpost.com/rss/local',
    'sports': 'https://feeds.washingtonpost.com/rss/sports',
    'national': 'https://feeds.washingtonpost.com/rss/national',
    'world': 'https://feeds.washingtonpost.com/rss/world',
    'business': 'https://feeds.washingtonpost.com/rss/business',
    'technology': 'https://feeds.washingtonpost.com/rss/business/technology',
    'lifestyle': 'https://feeds.washingtonpost.com/rss/lifestyle',
    'entertainment': 'https://feeds.washingtonpost.com/rss/entertainment',
    'climate': 'https://feeds.washingtonpost.com/rss/climate-environment',
    'health': 'https://feeds.washingtonpost.com/rss/health'
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
        # Add headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        
        # Create SSL context that ignores certificate verification
        context = create_ssl_context()
        
        # Open URL with custom SSL context
        response = urllib.request.urlopen(request, context=context)
        return ET.parse(source=response)
    except (HTTPError, URLError) as err:
        print(f"Network error while fetching {url}: {err}")
    except ET.ParseError as err:
        print(f"Error parsing XML from {url}: {err}")
    return None

def extract_images(item):
    """Extracts all available images from media:content and media:thumbnail tags."""
    images = []
    
    # Check for media:content images
    for media in item.findall('.//{http://search.yahoo.com/mrss/}content'):
        if 'url' in media.attrib and media.get('medium') == 'image':
            image_data = {
                'url': media.get('url'),
                'width': media.get('width'),
                'height': media.get('height'),
                'type': 'content'
            }
            # Extract description if available
            description = media.find('.//{http://search.yahoo.com/mrss/}description')
            if description is not None:
                image_data['description'] = description.text
            images.append(image_data)
    
    # Check for media:thumbnail
    for thumbnail in item.findall('.//{http://search.yahoo.com/mrss/}thumbnail'):
        if 'url' in thumbnail.attrib:
            images.append({
                'url': thumbnail.get('url'),
                'width': thumbnail.get('width'),
                'height': thumbnail.get('height'),
                'type': 'thumbnail'
            })
    
    return images

def get_wapo_articles(section, url):
    """Fetches and parses articles from Washington Post RSS feeds."""
    tree = fetch_rss_feed(url)
    if not tree:
        return None
        
    root = tree.getroot()
    articles = []
    
    # Find the correct path to items (usually in channel/item)
    channel = root.find('channel')
    if channel is None:
        return None
        
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
        
        # Extract author information
        author = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
        author = author.text if author is not None else None
        
        # Extract categories/tags
        categories = []
        for category in item.findall('category'):
            if category.text:
                categories.append(category.text)
        
        # Extract images
        images = extract_images(item)
        
        # Extract GUID
        guid = item.find('guid')
        guid = guid.text if guid is not None else None
        
        # Create article object
        article = {
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "author": author,
            "categories": categories,
            "images": images,
            "guid": guid
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

def scrape_wapo(section, url):
    """Scrapes articles for a given Washington Post section."""
    articles = get_wapo_articles(section, url)
    if articles:
        data = {
            "date": curr_date,
            "website": "WashingtonPost",
            "section": section,
            "articles": articles
        }
        write_json(data, 'WashingtonPost_articles.json')
        print(f"Downloaded articles from Washington Post section: {section}")
    else:
        error_data = {
            "date": curr_date,
            "website": "WashingtonPost",
            "section": section,
            "error": "Failed to download articles"
        }
        write_json(error_data, 'errorLog.json')
        print(f"Failed to download articles from Washington Post section: {section}")

def main():
    """Main function to start Washington Post scraping."""
    print("Starting Washington Post RSS feed scraper...")
    
    for section, url in WAPO_ARTICLE_URLS.items():
        scrape_wapo(section, url)
        # Random delay between requests to avoid overwhelming the server
        time.sleep(random.uniform(1.5, 3))
    
    print("Washington Post scraping completed!")

if __name__ == '__main__':
    main()