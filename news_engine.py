"""
TruthLens AI — News Engine
Fetches live news from NewsAPI + RSS fallback.
"""
import os, re, json, hashlib, logging, datetime, threading, time
import urllib.request, urllib.parse
import feedparser

logger = logging.getLogger(__name__)

_cache = {'news': [], 'breaking': [], 'last_fetch': 0}
_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutes

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/top-headlines"
FACT_CHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

RSS_FEEDS = {
    'india':         ['https://feeds.feedburner.com/ndtvnews-india-news',
                      'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
                      'https://www.thehindu.com/news/national/?service=rss'],
    'world':         ['https://feeds.bbci.co.uk/news/world/rss.xml',
                      'http://feeds.reuters.com/reuters/topNews'],
    'technology':    ['https://feeds.feedburner.com/TechCrunch',
                      'https://www.wired.com/feed/rss'],
    'business':      ['https://feeds.bbci.co.uk/news/business/rss.xml',
                      'http://feeds.reuters.com/reuters/businessNews'],
    'sports':        ['https://feeds.bbci.co.uk/sport/rss.xml'],
    'entertainment': ['https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'],
    'cybersecurity': ['https://feeds.feedburner.com/TheHackersNews',
                      'https://www.darkreading.com/rss.xml'],
    'ai':            ['https://feeds.feedburner.com/TechCrunch/artificial-intelligence'],
}

NEWSAPI_CATEGORIES = {
    'india':      {'country': 'in', 'category': 'general'},
    'world':      {'country': 'us', 'category': 'general'},
    'technology': {'country': 'us', 'category': 'technology'},
    'business':   {'country': 'in', 'category': 'business'},
    'sports':     {'country': 'in', 'category': 'sports'},
    'entertainment': {'country': 'in', 'category': 'entertainment'},
    'health':     {'country': 'us', 'category': 'health'},
    'science':    {'country': 'us', 'category': 'science'},
}

def _newsapi_fetch(api_key: str, category: str = 'general', country: str = 'in', page_size: int = 10) -> list:
    if not api_key: return []
    params = urllib.parse.urlencode({'apiKey': api_key, 'category': category, 'country': country, 'pageSize': page_size})
    url = f"{NEWSAPI_ENDPOINT}?{params}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TruthLensAI/2.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        articles = data.get('articles', [])
        result = []
        for a in articles:
            if not a.get('title') or a['title'] == '[Removed]': continue
            result.append({
                'title': a.get('title', ''),
                'summary': (a.get('description') or '')[:220],
                'link': a.get('url', '#'),
                'image': a.get('urlToImage', ''),
                'source': a.get('source', {}).get('name', 'NewsAPI'),
                'published': a.get('publishedAt', '')[:10],
                'category': category,
                'id': hashlib.md5(a.get('url', '').encode()).hexdigest()[:8]
            })
        return result
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed ({category}): {e}")
        return []

def _rss_fetch(category: str, feeds: list, limit: int = 4) -> list:
    items = []
    for url in feeds[:2]:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:limit]:
                title = e.get('title', '')
                if not title: continue
                items.append({
                    'title': title,
                    'summary': re.sub(r'<[^>]+>', '', e.get('summary', ''))[:220],
                    'link': e.get('link', '#'),
                    'image': '',
                    'source': feed.feed.get('title', 'RSS Feed'),
                    'published': e.get('published', datetime.date.today().isoformat())[:10],
                    'category': category,
                    'id': hashlib.md5(e.get('link', title).encode()).hexdigest()[:8]
                })
        except Exception as e:
            logger.debug(f"RSS fetch error {url}: {e}")
    return items

def fetch_all_news(news_api_key: str = '') -> dict:
    """Fetch news from all sources. Prefers NewsAPI, falls back to RSS."""
    all_news = []
    for cat, params in NEWSAPI_CATEGORIES.items():
        items = _newsapi_fetch(news_api_key, params['category'], params['country'], 6)
        if items:
            for i in items: i['category'] = cat
            all_news.extend(items)
        elif cat in RSS_FEEDS:
            all_news.extend(_rss_fetch(cat, RSS_FEEDS[cat]))

    # Extra RSS-only categories
    for cat in ['cybersecurity', 'ai']:
        if cat in RSS_FEEDS:
            all_news.extend(_rss_fetch(cat, RSS_FEEDS[cat], 3))

    if not all_news:
        all_news = _demo_news()

    return {
        'news': all_news[:50],
        'breaking': all_news[:5],
        'total': len(all_news),
        'source': 'NewsAPI' if news_api_key else 'RSS'
    }

def get_cached_news(news_api_key: str = '') -> dict:
    """Return cached news or refresh if stale."""
    global _cache
    now = time.time()
    with _lock:
        if now - _cache['last_fetch'] > CACHE_TTL or not _cache['news']:
            try:
                fresh = fetch_all_news(news_api_key)
                _cache['news'] = fresh['news']
                _cache['breaking'] = fresh['breaking']
                _cache['last_fetch'] = now
            except Exception as e:
                logger.error(f"News fetch failed: {e}")
                if not _cache['news']:
                    _cache['news'] = _demo_news()
                    _cache['breaking'] = _cache['news'][:3]
    return {'news': _cache['news'], 'breaking': _cache['breaking']}

def fact_check_query(claim: str, api_key: str) -> list:
    """Query Google Fact Check API for a claim."""
    if not api_key or not claim: return []
    params = urllib.parse.urlencode({'key': api_key, 'query': claim[:200], 'pageSize': 5})
    url = f"{FACT_CHECK_ENDPOINT}?{params}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TruthLensAI/2.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = []
        for item in data.get('claims', []):
            review = (item.get('claimReview') or [{}])[0]
            results.append({
                'claim': item.get('text', ''),
                'rating': review.get('textualRating', 'Unknown'),
                'publisher': review.get('publisher', {}).get('name', ''),
                'url': review.get('url', '#')
            })
        return results
    except Exception as e:
        logger.warning(f"Fact Check API error: {e}")
        return []

def _demo_news():
    today = datetime.date.today().strftime('%Y-%m-%d')
    return [
        {'title': 'India Economy Grows 8.4% in Q3 — Fastest Among G20 Nations', 'summary': 'India\'s GDP growth rate outpaces all major economies for the third consecutive quarter, driven by strong manufacturing and services sectors.', 'category': 'india', 'source': 'NDTV', 'link': '#', 'image': '', 'published': today, 'id': 'd1'},
        {'title': 'AI Breakthrough: New Model Achieves Human-Level Reasoning', 'summary': 'Researchers announce major milestone in artificial intelligence, with new large language model demonstrating advanced reasoning capabilities.', 'category': 'technology', 'source': 'TechCrunch', 'link': '#', 'image': '', 'published': today, 'id': 'd2'},
        {'title': 'Global Climate Summit: 195 Nations Sign Historic Agreement', 'summary': 'World leaders sign landmark climate deal committing to 50% emissions reduction by 2035, calling it the most significant climate action in history.', 'category': 'world', 'source': 'BBC', 'link': '#', 'image': '', 'published': today, 'id': 'd3'},
        {'title': 'Sensex Hits New All-Time High Amid FII Inflows', 'summary': 'Indian stock markets reach historic levels as foreign institutional investors pour funds into emerging market equities.', 'category': 'business', 'source': 'Times of India', 'link': '#', 'image': '', 'published': today, 'id': 'd4'},
        {'title': 'ISRO Successfully Launches Advanced Earth Observation Satellite', 'summary': 'India\'s space agency achieves another milestone with precision orbital insertion of its latest remote sensing spacecraft.', 'category': 'india', 'source': 'The Hindu', 'link': '#', 'image': '', 'published': today, 'id': 'd5'},
        {'title': 'Critical Zero-Day Vulnerability Discovered in Major Cloud Platforms', 'summary': 'Security researchers disclose a high-severity vulnerability affecting widely used cloud infrastructure, patches being deployed urgently.', 'category': 'cybersecurity', 'source': 'The Hacker News', 'link': '#', 'image': '', 'published': today, 'id': 'd6'},
        {'title': 'Gemini Ultra Surpasses GPT-4 on Multiple Benchmarks', 'summary': "Google's latest AI model sets new records across reasoning, coding, and multimodal understanding tasks in independent evaluations.", 'category': 'ai', 'source': 'Wired', 'link': '#', 'image': '', 'published': today, 'id': 'd7'},
        {'title': 'India Wins T20 Series Against Australia 3-2', 'summary': 'Indian cricket team clinches series victory with a dominant performance in the final match, boosting ICC rankings position.', 'category': 'sports', 'source': 'ESPN', 'link': '#', 'image': '', 'published': today, 'id': 'd8'},
    ]
