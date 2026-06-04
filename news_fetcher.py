"""
Live News Fetcher - Uses NewsAPI or fallback mock data
"""
import os, requests, random, datetime

NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

MOCK_ARTICLES = [
    {"title":"India's Tech Sector Records 18% Growth in Q3 2024","source":"The Hindu","category":"business","url":"#","publishedAt":"2024-01-15T09:00:00Z","description":"India's technology sector has recorded an impressive 18% growth in the third quarter, driven by increased AI adoption and digital transformation initiatives across industries.","image":"https://picsum.photos/seed/tech1/400/200"},
    {"title":"ISRO Successfully Tests New Satellite Communication System","source":"NDTV","category":"technology","url":"#","publishedAt":"2024-01-15T08:30:00Z","description":"The Indian Space Research Organisation has successfully tested its advanced satellite communication system, paving the way for next-generation internet connectivity across rural India.","image":"https://picsum.photos/seed/space1/400/200"},
    {"title":"India-UK Trade Deal Negotiations Enter Final Stage","source":"Reuters","category":"politics","url":"#","publishedAt":"2024-01-15T07:45:00Z","description":"Bilateral trade negotiations between India and the United Kingdom have entered their final stage, with officials confirming a deal could be signed within the next three months.","image":"https://picsum.photos/seed/trade1/400/200"},
    {"title":"AI Startup from Bengaluru Raises $50M Series B Funding","source":"India Today","category":"technology","url":"#","publishedAt":"2024-01-15T07:00:00Z","description":"A Bengaluru-based artificial intelligence startup focused on healthcare diagnostics has raised $50 million in Series B funding from global investors.","image":"https://picsum.photos/seed/startup1/400/200"},
    {"title":"Supreme Court Issues New Guidelines on Digital Privacy","source":"Times of India","category":"politics","url":"#","publishedAt":"2024-01-15T06:30:00Z","description":"The Supreme Court of India has issued comprehensive new guidelines on digital privacy, marking a landmark decision in the country's evolving data protection landscape.","image":"https://picsum.photos/seed/court1/400/200"},
    {"title":"Team India Wins Test Series Against Australia 3-1","source":"NDTV Sports","category":"sports","url":"#","publishedAt":"2024-01-14T20:00:00Z","description":"The Indian cricket team clinched the Test series against Australia with a commanding victory in the fourth Test, securing a 3-1 series win.","image":"https://picsum.photos/seed/cricket1/400/200"},
    {"title":"Global Climate Summit: 140 Nations Commit to Net Zero by 2050","source":"BBC","category":"world","url":"#","publishedAt":"2024-01-14T18:00:00Z","description":"Representatives from 140 nations have committed to achieving net-zero carbon emissions by 2050 at the global climate summit held in Geneva.","image":"https://picsum.photos/seed/climate1/400/200"},
    {"title":"New Cybersecurity Threat Targets Banking Apps Worldwide","source":"Reuters","category":"technology","url":"#","publishedAt":"2024-01-14T16:00:00Z","description":"Security researchers have identified a sophisticated new malware campaign targeting mobile banking applications across 45 countries.","image":"https://picsum.photos/seed/cyber1/400/200"},
    {"title":"WHO Approves New Malaria Vaccine for Sub-Saharan Africa","source":"BBC","category":"world","url":"#","publishedAt":"2024-01-14T14:00:00Z","description":"The World Health Organization has approved a new highly effective malaria vaccine for deployment across sub-Saharan Africa, potentially saving millions of lives.","image":"https://picsum.photos/seed/health1/400/200"},
    {"title":"Tesla Opens Gigafactory in Pune, Creates 15,000 Jobs","source":"Economic Times","category":"business","url":"#","publishedAt":"2024-01-14T12:00:00Z","description":"Tesla has officially inaugurated its first Indian Gigafactory in Pune, Maharashtra, which is expected to create over 15,000 direct employment opportunities.","image":"https://picsum.photos/seed/tesla1/400/200"},
    {"title":"Meta Unveils Next-Gen AR Glasses at CES 2024","source":"The Verge","category":"technology","url":"#","publishedAt":"2024-01-14T10:00:00Z","description":"Meta has unveiled its next-generation augmented reality glasses at CES 2024, featuring groundbreaking holographic display technology.","image":"https://picsum.photos/seed/meta1/400/200"},
    {"title":"RBI Holds Interest Rates Steady Amid Inflation Concerns","source":"Business Standard","category":"business","url":"#","publishedAt":"2024-01-14T09:00:00Z","description":"The Reserve Bank of India has decided to keep interest rates unchanged at its latest monetary policy meeting, citing persistent inflationary pressures.","image":"https://picsum.photos/seed/rbi1/400/200"},
]

BREAKING_NEWS = [
    "🔴 BREAKING: Major earthquake of magnitude 6.8 strikes Pacific region | Tsunami warning issued",
    "🔴 BREAKING: India's Sensex crosses 75,000 mark for first time in history",
    "🔴 BREAKING: UN Security Council calls emergency session on Middle East crisis",
    "🔴 BREAKING: New AI model beats human experts in medical diagnosis study",
    "🔴 BREAKING: G20 nations agree on new global digital taxation framework",
    "🔴 BREAKING: ISRO announces Chandrayaan-4 mission timeline for 2025",
    "🔴 BREAKING: Major cyberattack disrupts global banking systems; investigation underway",
    "🔴 BREAKING: India becomes world's 3rd largest economy by GDP",
]

class NewsFetcher:
    def fetch(self, category='general', country='in'):
        """Fetch news - tries NewsAPI first, falls back to mock data"""
        if NEWS_API_KEY:
            try:
                return self._fetch_from_api(category, country)
            except:
                pass
        return self._get_mock_news(category)
    
    def _fetch_from_api(self, category, country):
        url = 'https://newsapi.org/v2/top-headlines'
        params = {'apiKey': NEWS_API_KEY, 'country': country, 'category': category, 'pageSize': 10}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()
        articles = []
        for a in data.get('articles', []):
            if a.get('title') and a.get('description'):
                articles.append({
                    'title': a['title'],
                    'source': a.get('source', {}).get('name', 'Unknown'),
                    'description': a.get('description', ''),
                    'url': a.get('url', '#'),
                    'image': a.get('urlToImage') or f"https://picsum.photos/seed/{hash(a['title'])%100}/400/200",
                    'publishedAt': a.get('publishedAt', ''),
                    'category': category
                })
        return articles
    
    def _get_mock_news(self, category):
        articles = MOCK_ARTICLES.copy()
        if category != 'general':
            filtered = [a for a in articles if a['category'] == category]
            if filtered:
                articles = filtered
        random.shuffle(articles)
        return articles[:8]
    
    def get_breaking_news(self):
        return random.sample(BREAKING_NEWS, min(4, len(BREAKING_NEWS)))
