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

# The Guardian RSS feed sections
GUARDIAN_ARTICLE_URLS = (
    'world', 'uk-news', 'politics', 'business', 'technology',
    'science', 'environment', 'money', 'sport', 'football',
    'culture', 'books', 'film', 'music', 'education',
    'society', 'media', 'commentisfree', 'sustainable-business'
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

def extract_images(item):
    """Extracts all available image sizes from media:content tags."""
    images = []
    for media in item.findall('.//{http://search.yahoo.com/mrss/}content'):
        if 'url' in media.attrib:
            image_data = {
                'url': media.get('url'),
                'width': media.get('width'),
            }
            # Extract photographer credit if available
            credit = media.find('.//{http://search.yahoo.com/mrss/}credit')
            if credit is not None:
                image_data['credit'] = credit.text
            images.append(image_data)
    return images

def get_guardian_articles(section):
    """Fetches and parses articles from The Guardian RSS feeds."""
    url = f'https://www.theguardian.com/{section}/rss'
    
    tree = fetch_rss_feed(url)
    if not tree:
        return None
        
    root = tree.getroot()
    articles = []
    
    for item in root.findall('.//item'):
        # Extract title
        title = item.find('title').text if item.find('title') is not None else "No title"
        
        # Extract link
        link = item.find('link').text if item.find('link') is not None else None
        
        # Extract description and clean it up
        description = item.find('description')
        subline = description.text if description is not None else "No description"
        
        # Extract publication date
        pub_date = item.find('pubDate')
        pub_date = pub_date.text if pub_date is not None else None
        
        # Extract author
        author = item.find('.//{http://purl.org/dc/elements/1.1/}creator')
        author = author.text if author is not None else None
        
        # Extract categories
        categories = []
        for category in item.findall('category'):
            if 'domain' in category.attrib:
                categories.append({
                    'name': category.text,
                    'domain': category.get('domain')
                })
        
        # Extract all available images
        images = extract_images(item)
        
        # Create article object with all metadata
        article = {
            "title": title,
            "link": link,
            "subline": subline,
            "pub_date": pub_date,
            "author": author,
            "categories": categories,
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

def scrape_guardian(section):
    """Scrapes articles for a given Guardian section."""
    articles = get_guardian_articles(section)
    if articles:
        data = {
            "date": curr_date,
            "website": "Guardian",
            "section": section,
            "articles": articles
        }
        write_json(data, 'Guardian_articles.json')
        print(f"Downloaded articles from Guardian section: {section}")
    else:
        error_data = {
            "date": curr_date,
            "website": "Guardian",
            "section": section,
            "error": "Failed to download articles"
        }
        write_json(error_data, 'errorLog.json')
        print(f"Failed to download articles from Guardian section: {section}")

def main():
    """Main function to start Guardian scraping."""
    print("Starting The Guardian RSS feed scraper...")
    
    for section in GUARDIAN_ARTICLE_URLS:
        scrape_guardian(section)
        # Random delay between requests to avoid overwhelming the server
        time.sleep(random.uniform(1, 2))
    
    print("Guardian scraping completed!")

if __name__ == '__main__':
    main()