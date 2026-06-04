"""TruthLens AI — Advanced URL Scraper with BeautifulSoup"""
import re, logging, urllib.request, urllib.parse
logger = logging.getLogger(__name__)

def scrape_url(url: str, timeout: int = 12) -> dict:
    """Scrape article text from URL. Returns dict with success, text, title, error."""
    if not url or not url.startswith(('http://', 'https://')):
        return {'success': False, 'error': 'Invalid URL format'}
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode('utf-8', errors='ignore')

        # Try BeautifulSoup first
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw, 'lxml')
            for tag in soup(['script','style','nav','footer','header','aside','form','iframe']):
                tag.decompose()
            title = soup.title.string.strip() if soup.title else ''
            # Get article body
            article = soup.find('article') or soup.find('main') or soup.find(class_=re.compile(r'article|content|body|story|post', re.I)) or soup.body
            text = article.get_text(separator=' ', strip=True) if article else soup.get_text(separator=' ', strip=True)
        except ImportError:
            # Regex fallback
            title_m = re.search(r'<title[^>]*>(.*?)</title>', raw, re.I|re.S)
            title = title_m.group(1).strip() if title_m else ''
            text = re.sub(r'<[^>]+>', ' ', raw)

        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        text = text[:5000]  # cap at 5000 chars

        if len(text) < 50:
            return {'success': False, 'error': 'Could not extract meaningful text from this page'}

        return {'success': True, 'text': text, 'title': title[:200], 'length': len(text)}
    except urllib.error.HTTPError as e:
        return {'success': False, 'error': f'HTTP {e.code}: {e.reason}'}
    except urllib.error.URLError as e:
        return {'success': False, 'error': f'Connection failed: {str(e.reason)[:80]}'}
    except Exception as e:
        return {'success': False, 'error': str(e)[:120]}
