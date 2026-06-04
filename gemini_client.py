"""Gemini AI client — fact-checking, chatbot, analysis"""
import os, re, json, requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def _call_gemini(prompt, max_tokens=800):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    payload = {"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":max_tokens,"temperature":0.3}}
    r = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def gemini_analyze_news(text):
    prompt = f"""You are an expert AI fact-checker. Analyze this news text and respond ONLY with valid JSON (no markdown fences):
{{"verdict":"FAKE or REAL or MISLEADING or UNVERIFIED","confidence":<0-100>,"summary":"<2-sentence summary>","reasoning":"<3-5 sentence expert explanation>","red_flags":["<flag>"],"emotional_manipulation":<true/false>,"propaganda_signals":<true/false>,"clickbait_score":<0-10>,"credibility_score":<0-100>,"suggested_sources":["BBC","Reuters"]}}

News text: \"\"\"{text[:3000]}\"\"\""""
    try:
        raw = re.sub(r"```json|```","",_call_gemini(prompt,600)).strip()
        return json.loads(raw)
    except Exception as e:
        return {"error":str(e),"verdict":"UNVERIFIED","confidence":50,"summary":"","reasoning":"Gemini analysis unavailable.","red_flags":[],"credibility_score":50,"clickbait_score":0,"emotional_manipulation":False,"propaganda_signals":False,"suggested_sources":["BBC","Reuters","NDTV"]}

def gemini_chat(message, history=None):
    history_text = ""
    if history:
        for h in (history[-4:]):
            history_text += f"{'User' if h['role']=='user' else 'ARIA'}: {h['content']}\n"
    prompt = f"""You are ARIA (AI Research Intelligence Assistant) for TruthLens AI fake news detection platform.
Be expert, friendly, brief (max 4 sentences unless asked more). Support English/Hindi/Hinglish. Use emojis sparingly.
Recent chat:\n{history_text}\nUser: {message}\nARIA:"""
    try:
        return _call_gemini(prompt, 300)
    except Exception as e:
        return f"Sorry, I'm having trouble connecting right now. Please try again! 🙏"

def gemini_analyze_url(text, url):
    prompt = f"""Analyze this news article. Return ONLY valid JSON (no markdown):
{{"title":"<headline>","verdict":"FAKE or REAL or MISLEADING or UNVERIFIED","confidence":<0-100>,"credibility_score":<0-100>,"clickbait_detected":<true/false>,"summary":"<2 sentences>","reasoning":"<3 sentences>","red_flags":["..."],"trusted_source_match":<true/false>}}
URL: {url}\nArticle: \"\"\"{text[:2500]}\"\"\""""
    try:
        raw = re.sub(r"```json|```","",_call_gemini(prompt,500)).strip()
        return json.loads(raw)
    except Exception as e:
        return {"error":str(e),"verdict":"UNVERIFIED","confidence":50,"credibility_score":50,"clickbait_detected":False,"red_flags":[],"summary":"","reasoning":"Gemini unavailable.","trusted_source_match":False,"title":"Unknown"}
