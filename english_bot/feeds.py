import feedparser
import re
import logging
from english_bot.dedup import normalize_url

logger = logging.getLogger(__name__)

def clean_summary(raw_html: str, max_chars: int = 400) -> str:
    """Removes HTML tags and normalizes whitespace in the feed summary."""
    if not raw_html:
        return ""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    # Replace multiple spaces/newlines with a single space
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    # Trim to max_chars
    if len(clean_text) > max_chars:
        clean_text = clean_text[:max_chars].rsplit(' ', 1)[0] + "..."
    return clean_text

# Headers to avoid blocks (e.g. 403 Forbidden)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

FEEDS_BY_TOPIC = {
    "Science & Space": [
        "https://www.snexplores.org/feed/",
        "https://earthsky.org/feed/",
        "https://www.nasa.gov/rss/image_of_the_day.rss",
        "https://www.nasa.gov/rss/breaking_news.rss",
        "https://www.sciencedaily.com/rss/space_time.xml",
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.newsinlevels.com/category/information/feed/",
        "https://learningenglish.voanews.com/api/zmg_pl-vomx-tpeymtm"
    ],
    "Nature & Creative": [
        "https://www.sciencejournalforkids.org/feed/",
        "https://www.sciencedaily.com/rss/plants_animals.xml",
        "https://kidsactivitiesblog.com/feed/",
        "https://thekidshouldseethis.com/feed",
        "https://earthobservatory.nasa.gov/feeds/earth-observatory.rss",
        "https://www.newsinlevels.com/category/nature/feed/",
        "https://www.newsinlevels.com/category/sport/feed/",
        "https://www.newsinlevels.com/category/exercises/feed/"
    ],
    "History, Culture & World": [
        "https://newsforkids.net/feed/",
        "https://www.smithsonianmag.com/rss/smart-news/",
        "https://www.smithsonianmag.com/rss/history/",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.newsinlevels.com/category/news/feed/",
        "https://www.newsinlevels.com/category/history/feed/",
        "https://www.newsinlevels.com/category/interesting/feed/",
        "https://www.newsinlevels.com/category/funny/feed/",
        "https://learningenglish.voanews.com/api/zoroqql-vomx-tpeptpqq",
        "https://learningenglish.voanews.com/api/zmypyl-vomx-tpeyry_",
        "https://learningenglish.voanews.com/api/zyg__l-vomx-tpetmty",
        "https://learningenglish.voanews.com/api/zkm-ql-vomx-tpej-rqi",
        "https://learningenglish.voanews.com/api/zj_pvl-vomx-tpebb_v"
    ]
}

import requests

def fetch_articles(topic_name: str = None, max_items: int = 100) -> list[dict]:
    """Fetches articles from all RSS feeds associated with the topic_name or a general fallback list."""
    urls = FEEDS_BY_TOPIC.get(topic_name)
    if not urls:
        logger.info(f"Topic '{topic_name}' not found in FEEDS_BY_TOPIC. Using fallback general feeds.")
        urls = [
            "https://newsforkids.net/feed/",
            "https://www.snexplores.org/feed/",
            "https://earthsky.org/feed/",
            "https://thekidshouldseethis.com/feed",
            "https://www.newsinlevels.com/feed/"
        ]

    articles = []
    seen_urls = set()
    
    # Calculate how many items to fetch per feed to avoid overloading but gather enough variety
    max_per_feed = max(3, max_items // len(urls) + 1)
    
    for url in urls:
        logger.info(f"Fetching RSS feed from: {url}")
        try:
            # Use requests with headers to bypass potential Cloudflare or basic UA blocks
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                continue
                
            feed = feedparser.parse(response.text)
            
            # Check for parsing errors
            if getattr(feed, "bozo", 0) == 1 and not feed.entries:
                logger.warning(f"Bozo parsing issue with feed: {url}")
                
            feed_articles_count = 0
            for entry in feed.entries:
                if feed_articles_count >= max_per_feed:
                    break
                    
                title = entry.get("title", "Untitled").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                
                if not link:
                    continue
                    
                normalized_link = normalize_url(link)
                if normalized_link in seen_urls:
                    continue
                    
                seen_urls.add(normalized_link)
                articles.append({
                    "title": title,
                    "url": normalized_link,
                    "summary": clean_summary(summary)
                })
                feed_articles_count += 1
                
            logger.info(f"Fetched {feed_articles_count} articles from {url}")
        except Exception as e:
            logger.error(f"Error fetching from feed '{url}': {e}")
            
    logger.info(f"Total articles fetched across all feeds: {len(articles)}")
    return articles[:max_items]
