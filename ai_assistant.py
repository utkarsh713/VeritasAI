"""
AI Assistant - Powered by Anthropic Claude API
Handles chatbot interactions for VeritasAI
"""

import os
import requests
import json

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

SYSTEM_PROMPT = """You are VeritasAI Assistant — an expert AI news analyst and fact-checker embedded in VeritasAI, India's most advanced fake news detection platform.

Your personality:
- Professional yet friendly, like a knowledgeable senior journalist
- Precise, evidence-based, never sensational
- You speak clearly about misinformation without political bias
- You're optimistic about truth-finding and media literacy

Your capabilities:
- Explain why news may be fake or real
- Summarize complex news stories
- Suggest trusted news sources (BBC, NDTV, Reuters, The Hindu, Indian Express, etc.)
- Teach media literacy skills
- Explain AI/ML concepts simply
- Guide users on the VeritasAI platform

Key rules:
- Never take political sides
- Always recommend verification from multiple sources
- Be concise — 2-4 paragraphs max unless asked for more
- Use markdown formatting with bullets and bold for clarity
- If asked about a specific claim, analyze it logically
- For Indian news, reference PIB, NDTV, The Hindu, Indian Express as trusted sources
- Always promote media literacy and critical thinking

You are not able to browse the internet in real-time, but you have extensive knowledge about media, journalism, and misinformation patterns."""

FALLBACK_RESPONSES = {
    'fake': [
        "Great question! Fake news typically exhibits **3 core patterns**:\n\n• **Sensational language**: Words like 'SHOCKING', 'You won't believe' trigger emotional reactions before rational thinking\n• **Missing attribution**: Real journalism names sources. Fake content says 'sources say' without specifics\n• **Urgency engineering**: 'Share before it's deleted!' — designed to bypass your fact-checking instinct\n\nOur AI detects these patterns with over 85% accuracy using NLP analysis.",
    ],
    'default': [
        "I'm VeritasAI Assistant! 🤖 I can help you:\n\n• **Analyze news** for fake patterns\n• **Find trusted sources** for any topic\n• **Explain our AI** detection methodology\n• **Answer questions** about media literacy\n\nWhat would you like to know?",
        "That's an interesting question! In the world of media intelligence, critical thinking is your most powerful tool. Always ask: **Who published this? What evidence do they cite? Can I verify this elsewhere?**\n\nFeel free to paste any news article in the Analyzer tab — our AI will assess it instantly!",
    ],
}


class AIAssistant:
    def __init__(self):
        self.api_key = ANTHROPIC_API_KEY
        self.base_url = 'https://api.anthropic.com/v1/messages'

    def respond(self, message, history=None):
        """Generate AI response"""
        if self.api_key:
            try:
                return self._call_anthropic(message, history or [])
            except Exception as e:
                pass
        return self._fallback_response(message)

    def _call_anthropic(self, message, history):
        """Call Anthropic Claude API"""
        messages = []
        # Add conversation history
        for h in history[-6:]:  # Last 6 turns
            messages.append({'role': h['role'], 'content': h['content']})
        messages.append({'role': 'user', 'content': message})

        payload = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 600,
            'system': SYSTEM_PROMPT,
            'messages': messages,
        }

        resp = requests.post(
            self.base_url,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
            },
            json=payload,
            timeout=15,
        )

        data = resp.json()
        if 'content' in data and data['content']:
            return data['content'][0].get('text', '')
        raise Exception('No content in response')

    def _fallback_response(self, message):
        """Smart rule-based fallback"""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ['fake', 'misinformation', 'disinformation', 'hoax']):
            return FALLBACK_RESPONSES['fake'][0]

        if any(w in msg_lower for w in ['hello', 'hi', 'hey', 'namaste', 'help']):
            return FALLBACK_RESPONSES['default'][0]

        if any(w in msg_lower for w in ['source', 'trust', 'reliable', 'credible']):
            return "**Trusted News Sources I Recommend:**\n\n🇮🇳 **India**: NDTV, The Hindu, Indian Express, Mint, Wire, Scroll.in\n🌍 **International**: BBC, Reuters, AP News, Guardian, Al Jazeera\n✅ **Fact-Checkers**: AltNews, FactCheck.in, Snopes, PolitiFact, AFP Fact Check\n\nFor breaking news, always cross-reference at least 2-3 independent sources before forming opinions or sharing."

        if any(w in msg_lower for w in ['how', 'what', 'why', 'when', 'where', 'who']):
            return f"That's a thoughtful question! While I'm working in offline mode right now (connect an API key for full AI capabilities), I can tell you that **media literacy** starts with asking exactly those kinds of questions.\n\n**Quick tips for '{message[:50]}...':**\n• Search multiple reputable outlets\n• Check the publication date\n• Look for expert quotes and citations\n• Use our analyzer to check any news text you find!"

        return FALLBACK_RESPONSES['default'][1]
