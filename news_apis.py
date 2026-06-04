"""
Live news: NewsAPI + GDELT + RSS fallback
Google Fact Check API
"""
import os, re, json, hashlib, datetime, requests, feedparser

NEWS_API_KEY         = os.getenv("NEWS_API_KEY", "")
GOOGLE_FACTCHECK_KEY = os.getenv("GOOGLE_FACTCHECK_KEY", "")

RSS_FEEDS = {
    "india":         ["https://feeds.feedburner.com/ndtvnews-india-news","https://timesofindia.indiatimes.com/rssfeeds/296589292.cms","https://www.thehindu.com/news/national/?service=rss"],
    "world":         ["https://feeds.bbci.co.uk/news/world/rss.xml","https://feeds.reuters.com/reuters/topNews"],
    "technology":    ["https://feeds.feedburner.com/TechCrunch","https://www.wired.com/feed/rss","https://feeds.bbci.co.uk/news/technology/rss.xml"],
    "business":      ["https://feeds.bbci.co.uk/news/business/rss.xml","https://feeds.reuters.com/reuters/businessNews"],
    "sports":        ["https://feeds.bbci.co.uk/sport/rss.xml","https://timesofindia.indiatimes.com/rssfeeds/4719161.cms"],
    "entertainment": ["https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"],
    "cybersecurity": ["https://feeds.feedburner.com/TheHackersNews","https://www.darkreading.com/rss.xml"],
    "politics":      ["https://feeds.bbci.co.uk/news/politics/rss.xml","https://feeds.reuters.com/Reuters/PoliticsNews"],
    "ai":            ["https://feeds.feedburner.com/TechCrunch/startups","https://venturebeat.com/category/ai/feed/"],
}

def fetch_rss_news(categories=None, limit=6):
    cats = categories or list(RSS_FEEDS.keys())
    items = []
    for cat in cats:
        for url in RSS_FEEDS.get(cat, [])[:1]:
            try:
                feed = feedparser.parse(url)
                source = feed.feed.get("title","Unknown")
                for e in feed.entries[:limit]:
                    summary = re.sub("<[^>]+>","",e.get("summary",""))[:220]
                    items.append({
                        "id":       hashlib.md5(e.get("link","").encode()).hexdigest()[:8],
                        "title":    e.get("title",""),
                        "summary":  summary,
                        "link":     e.get("link","#"),
                        "category": cat,
                        "source":   source,
                        "published":e.get("published", datetime.datetime.now().strftime("%b %d, %Y")),
                        "image":    _extract_image(e),
                    })
            except Exception:
                pass
    return items

def fetch_newsapi(category="general", q=None, limit=10):
    if not NEWS_API_KEY:
        return []
    try:
        params = {"apiKey": NEWS_API_KEY, "pageSize": limit, "language": "en"}
        if q:   params["q"] = q
        else:   params["category"] = category; params["country"] = "us"
        r = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
        articles = r.json().get("articles", [])
        return [{
            "id":       hashlib.md5(a.get("url","").encode()).hexdigest()[:8],
            "title":    a.get("title",""),
            "summary":  (a.get("description") or "")[:220],
            "link":     a.get("url","#"),
            "category": category,
            "source":   a.get("source",{}).get("name","NewsAPI"),
            "published":a.get("publishedAt","")[:10],
            "image":    a.get("urlToImage",""),
        } for a in articles if a.get("title")]
    except Exception:
        return []

def google_factcheck(query):
    """Search Google Fact Check Tools API for a claim."""
    if not GOOGLE_FACTCHECK_KEY:
        return []
    try:
        r = requests.get(
            "https://factchecktools.googleapis.com/v1alpha1/claims:search",
            params={"query": query[:200], "key": GOOGLE_FACTCHECK_KEY, "pageSize": 5},
            timeout=10
        )
        claims = r.json().get("claims", [])
        results = []
        for c in claims:
            review = c.get("claimReview", [{}])[0]
            results.append({
                "claim":     c.get("text",""),
                "claimant":  c.get("claimant",""),
                "rating":    review.get("textualRating",""),
                "publisher": review.get("publisher",{}).get("name",""),
                "url":       review.get("url",""),
            })
        return results
    except Exception:
        return []

def _extract_image(entry):
    """Try to pull image URL from RSS entry."""
    if hasattr(entry,"media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url","")
    if hasattr(entry,"media_content") and entry.media_content:
        return entry.media_content[0].get("url","")
    return ""

def get_demo_news():
    now = datetime.datetime.now().strftime("%b %d, %Y")
    return [
        {"id":"d1","title":"India Achieves Record GDP Growth in Q3 2024","summary":"India's economy grows at 8.4%, fastest among major economies globally...","category":"india","source":"NDTV","link":"#","published":now,"image":""},
        {"id":"d2","title":"AI Breakthrough: New Model Surpasses Human Reasoning Benchmarks","summary":"Researchers announce major milestone in artificial general intelligence...","category":"ai","source":"TechCrunch","link":"#","published":now,"image":""},
        {"id":"d3","title":"Global Climate Summit Reaches Historic Emissions Agreement","summary":"195 nations sign landmark deal to cut emissions by 50% by 2035...","category":"world","source":"BBC","link":"#","published":now,"image":""},
        {"id":"d4","title":"Sensex Crosses New All-Time High Amid Strong FII Inflows","summary":"Indian stock market reaches historic milestone fuelled by foreign investment...","category":"business","source":"Times of India","link":"#","published":now,"image":""},
        {"id":"d5","title":"ISRO Successfully Launches Earth Observation Satellite","summary":"India's space agency achieves precision orbit insertion for latest mission...","category":"india","source":"The Hindu","link":"#","published":now,"image":""},
        {"id":"d6","title":"Major Zero-Day Vulnerability Discovered in Popular Software","summary":"Security researchers disclose critical flaw affecting millions of devices worldwide...","category":"cybersecurity","source":"Wired","link":"#","published":now,"image":""},
        {"id":"d7","title":"Lok Sabha Passes New Digital Regulation Bill","summary":"Parliament approves landmark legislation governing social media platforms in India...","category":"politics","source":"India Today","link":"#","published":now,"image":""},
        {"id":"d8","title":"Champions League Final: Drama at the Last Minute","summary":"Thrilling finale produces stunning upset as underdog team claims title...","category":"sports","source":"ESPN","link":"#","published":now,"image":""},
    ]
