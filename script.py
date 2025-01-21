import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
import urllib.request
import threading
import datetime
import random
import time
import json

# Current date for logging and file naming
date = datetime.datetime.now()
curr_date = f"{date.day}/{date.month}/{date.year}"

# Directories for news sources
BBC_ARTICLE_URLS = (
    'world', 'uk', 'business', 'politics', 'health',
    'education', 'science_and_environment', 'technology', 'entertainment_and_arts',
    'world/africa', 'world/asia', 'world/europe', 'world/latin_america', 'world/middle_east',
    'world/us_and_canada', 'england', 'northern_ireland', 'scotland', 'wales'
)

CNN_ARTICLE_URLS = (
    'edition', 'edition_world', 'edition_africa', 'edition_americas',
    'edition_asia', 'edition_europe', 'edition_meast', 'edition_us', 'money_news_international',
    'edition_technology', 'edition_space', 'edition_entertainment', 'edition_sport',
    'edition_football', 'edition_golf', 'edition_motorsport', 'edition_tennis'
)

RT_ARTICLE_URLS = ('news', 'uk', 'usa', 'sport', 'russia', 'business')


def fetch_rss_feed(url):
    """Fetches and parses an RSS feed from a URL."""
    try:
        return ET.parse(source=urllib.request.urlopen(url))
    except (HTTPError, URLError) as err:
        print(f"Network error while fetching {url}: {err}")
    except ET.ParseError as err:
        print(f"Error parsing XML from {url}: {err}")
    return None


def get_articles(dir, website):
    """Fetches and parses articles for a given directory and website."""
    url = None
    if website == 'BBC':
        url = f'http://feeds.bbci.co.uk/news/{dir}/rss.xml'
    elif website == 'CNN':
        url = f'http://rss.cnn.com/rss/{dir}.rss'
    elif website == 'RT':
        url = f'https://www.rt.com/rss/{dir}'
    elif website == 'guardian':
        url = 'https://www.theguardian.com/sitemaps/news.xml'

    tree = fetch_rss_feed(url)
    if not tree:
        return None

    root = tree.getroot()
    articles = []
    for item in root.iter('item'):
        title = item.find('title').text if item.find('title') is not None else "No title"
        image = None
        subline = item.find('description').text if item.find('description') is not None else "No description"
        media_content = item.find('{http://search.yahoo.com/mrss/}content')
        if media_content is not None and 'url' in media_content.attrib:
            image = media_content.attrib['url']

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


def scrape(dir, website):
    """Scrapes articles for a given directory and website."""
    articles = get_articles(dir, website)
    if articles:
        data = {
            "date": curr_date,
            "website": website,
            "dir": dir,
            "articles": articles
        }
        write_json(data, f'{website}_articles.json')
        print(f"Downloaded articles from section: {website} - {dir}")
    else:
        error_data = {
            "date": curr_date,
            "website": website,
            "dir": dir,
            "error": "Failed to download articles"
        }
        write_json(error_data, 'errorLog.json')
        print(f"Failed to download articles from section: {dir}")


def bbc_control():
    """Controls scraping for BBC sections."""
    for target in BBC_ARTICLE_URLS:
        scrape(target, 'BBC')
        time.sleep(random.uniform(0.5, 1.5))


def cnn_control():
    """Controls scraping for CNN sections."""
    for target in CNN_ARTICLE_URLS:
        scrape(target, 'CNN')
        time.sleep(random.uniform(0.5, 1.5))


def rt_control():
    """Controls scraping for RT sections."""
    for target in RT_ARTICLE_URLS:
        scrape(target, 'RT')
        time.sleep(random.uniform(0.5, 1.5))


def guardian_control():
    """Controls scraping for Guardian."""
    scrape('titles', 'guardian')
    scrape('keywords', 'guardian')


def main():
    """Main function to start scraping."""
    threads = [
        threading.Thread(target=bbc_control),
        threading.Thread(target=cnn_control),
        threading.Thread(target=guardian_control),
        threading.Thread(target=rt_control)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
