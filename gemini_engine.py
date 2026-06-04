"""TruthLens AI — Gemini API Engine for AI fact-checking + chatbot"""
import os, json, re, datetime
import urllib.request, urllib.parse

GEMINI_KEY = os.environ.get('GEMINI_API_KEY','')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

def _call(prompt, max_tokens=1024, temperature=0.3):
    if not GEMINI_KEY:
        return None, "GEMINI_API_KEY not set"
    payload = json.dumps({'contents':[{'parts':[{'text':prompt}]}],
                          'generationConfig':{'maxOutputTokens':max_tokens,'temperature':temperature}}).encode()
    req = urllib.request.Request(f"{GEMINI_URL}?key={GEMINI_KEY}",
                                  data=payload, headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            text = data['candidates'][0]['content']['parts'][0]['text']
            return text.strip(), None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return None, f"Gemini HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return None, str(e)

def ai_fact_check(text: str, ml_result: dict) -> dict:
    """Deep AI analysis of news content using Gemini."""
    prompt = f"""You are an expert fact-checker and misinformation analyst. Analyze the following news text critically.

NEWS TEXT:
\"\"\"{text[:2000]}\"\"\"

ML MODEL RESULT: {ml_result.get('prediction','UNKNOWN')} (confidence: {ml_result.get('confidence',0)}%)

Provide a detailed analysis in the following JSON format ONLY (no markdown, just JSON):
{{
  "verdict": "LIKELY_FAKE" | "LIKELY_REAL" | "MISLEADING" | "UNVERIFIABLE" | "SATIRE",
  "confidence": <0-100 integer>,
  "summary": "<2-3 sentence plain English verdict>",
  "reasoning": "<detailed paragraph explaining why this may or may not be credible>",
  "manipulation_tactics": ["<tactic1>", "<tactic2>"],
  "missing_context": "<what context or facts are missing>",
  "suggested_queries": ["<search query to verify>", "<another query>"],
  "trusted_sources": ["<source to check>", "<another source>"],
  "red_flags_ai": ["<specific flag found in text>"],
  "credibility_breakdown": {{
    "language_score": <0-100>,
    "source_score": <0-100>,
    "factual_score": <0-100>,
    "emotional_score": <0-100>
  }}
}}"""
    resp, err = _call(prompt, max_tokens=1200, temperature=0.2)
    if err or not resp:
        return {'error': err or 'No response', 'available': False}
    try:
        clean = re.sub(r'```json|```','', resp).strip()
        data = json.loads(clean)
        data['available'] = True
        data['analyzed_by'] = 'Gemini 1.5 Flash'
        data['timestamp'] = datetime.datetime.now().isoformat()
        return data
    except Exception as e:
        return {'available': True, 'raw': resp, 'parse_error': str(e),
                'summary': resp[:500], 'verdict': 'UNVERIFIABLE', 'confidence': 50}

def ai_chat(message: str, history: list = []) -> str:
    """Gemini-powered ARIA chatbot."""
    hist_text = '\n'.join([f"{'User' if m['role']=='user' else 'ARIA'}: {m['content']}" for m in history[-6:]])
    prompt = f"""You are ARIA (AI Research Intelligence Assistant), a highly intelligent assistant embedded in TruthLens AI — a fake news detection and media intelligence platform.

Your personality: Professional yet friendly, knowledgeable about media literacy, fact-checking, AI/ML, Indian and global news. You support English, Hindi, and Hinglish.

Platform capabilities you can discuss:
- Fake news detection using TF-IDF + Logistic Regression + Gemini AI
- Live news from BBC, NDTV, Reuters, TechCrunch
- URL article analysis
- Image deepfake detection
- Firebase user accounts and saved history

Previous conversation:
{hist_text}

User message: {message}

Respond helpfully in 2-4 sentences max (unless user asks for detail). Use emojis sparingly. If asked in Hindi/Hinglish, reply in kind. Never say you are Google's Gemini; you are ARIA by TruthLens AI."""
    resp, err = _call(prompt, max_tokens=400, temperature=0.7)
    if err:
        return _fallback_chat(message)
    return resp or _fallback_chat(message)

def summarize_article(text: str) -> dict:
    """Summarize a news article with AI."""
    prompt = f"""Summarize this news article in JSON format (no markdown):
{{
  "headline": "<one line summary>",
  "key_points": ["<point1>", "<point2>", "<point3>"],
  "tone": "neutral" | "sensational" | "analytical" | "opinionated",
  "topics": ["<topic1>", "<topic2>"],
  "summary": "<2-3 sentence summary>"
}}

Article: {text[:3000]}"""
    resp, err = _call(prompt, max_tokens=600, temperature=0.3)
    if err or not resp:
        return {'error': err, 'available': False}
    try:
        clean = re.sub(r'```json|```','',resp).strip()
        data = json.loads(clean); data['available'] = True; return data
    except:
        return {'available': True, 'summary': resp[:400], 'headline': 'Article Summary'}

def detect_clickbait(headline: str) -> dict:
    """Analyze headline for clickbait patterns."""
    prompt = f"""Analyze this headline for clickbait in JSON (no markdown):
{{"is_clickbait": true/false, "score": <0-100>, "reason": "<why>", "rewritten": "<neutral version>"}}
Headline: {headline}"""
    resp, err = _call(prompt, max_tokens=200, temperature=0.2)
    if err or not resp:
        return {'is_clickbait': False, 'score': 0, 'available': False}
    try:
        clean = re.sub(r'```json|```','',resp).strip()
        data = json.loads(clean); data['available'] = True; return data
    except:
        return {'available': True, 'raw': resp[:200], 'is_clickbait': False, 'score': 0}

def _fallback_chat(msg):
    m = msg.lower()
    if any(w in m for w in ['hello','hi','hey','namaste']): return "🤖 Namaste! I'm ARIA, your AI Research Intelligence Assistant. I can help detect fake news, explain articles, suggest trusted sources, and answer questions about media literacy. How can I help?"
    if 'fake' in m or 'detect' in m: return "🔍 Paste any news text in the Analyzer section. Our AI uses TF-IDF + Logistic Regression + Gemini AI to detect fake news with high accuracy. We also check red flags like emotional language and conspiracy terms."
    if 'source' in m or 'trust' in m: return "✅ Trusted sources: BBC, Reuters, AP News, The Hindu, NDTV, Times of India, TechCrunch, Wired. Always verify a story across 2-3 independent sources before sharing!"
    if 'how' in m: return "⚙️ TruthLens AI uses NLP preprocessing → TF-IDF vectorization → Logistic Regression + PassiveAggressive Classifier ensemble, plus Gemini AI for deep reasoning. Red flag detection catches emotional manipulation, vague sources, and conspiracy language."
    return "🤔 I'm ARIA — I can help with fake news detection, media literacy, trusted sources, and news analysis. What would you like to know?"
