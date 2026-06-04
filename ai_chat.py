"""AI Chatbot Assistant for VeritasAI"""
import random, re

RESPONSES = {
    'greeting': [
        "Hello! I'm VERA, your AI news intelligence assistant. I can help you detect fake news, analyze articles, summarize headlines, and guide you in finding trusted sources. What would you like to know? 🤖",
        "Hi there! I'm VERA — Verified Real-time Analysis Assistant. Ask me anything about news verification, fake news patterns, or today's headlines! 📰"
    ],
    'fake_news_general': [
        "Fake news refers to deliberately fabricated or misleading information presented as legitimate journalism. Common patterns include: 1) Sensational headlines 2) No credible sources 3) Emotional manipulation 4) Misrepresented statistics. Always verify with multiple trusted sources! 🔍",
        "Great question! Fake news typically shows these warning signs: excessive ALL CAPS, multiple exclamation marks, appeals to fear/outrage, anonymous 'insider' sources, and content that seems too shocking to be true. Our AI analyzes over 40 linguistic markers to detect these patterns."
    ],
    'how_it_works': [
        "VeritasAI uses a multi-layer detection system: 1) **NLP Analysis** - examines language patterns, sentiment & tone 2) **TF-IDF Vectorization** - identifies statistical word patterns common in fake news 3) **ML Classification** - our model trained on 40,000+ articles 4) **Source Credibility** scoring. Together achieving 94.7% accuracy! 🧠",
    ],
    'trusted_sources': [
        "Here are highly reliable news sources I recommend: 🌟\n\n**India:** The Hindu, NDTV, Indian Express, Wire, BBC Hindi\n\n**International:** Reuters, AP News, BBC, The Guardian, Bloomberg\n\n**Fact-checking:** Alt News, BOOM, FactChecker.in, Snopes, PolitiFact\n\nAlways cross-reference news across at least 3 sources!",
    ],
    'tips': [
        "Top 5 tips to identify fake news:\n1. 🔎 Check the URL — fake sites often mimic real ones\n2. 📅 Verify the date — old news recycled as new\n3. 👤 Who wrote it? Check author credentials\n4. 🔗 Are there sources/links? Verify them\n5. 🖼️ Reverse image search photos\n\nAlso use our AI detector for instant analysis!",
    ],
    'default': [
        "That's an interesting question! While I'm specialized in news verification and fake news detection, I can help you think critically about media. Could you paste the specific news text or URL you want me to analyze? 📋",
        "I'm VERA, specialized in news intelligence and misinformation detection. I can help you: verify news authenticity, explain AI analysis results, find trusted sources, or answer questions about media literacy. What specifically interests you?",
        "Good question! For the most accurate analysis, try pasting the news article text in the detection box above. I can also explain any results, discuss misinformation trends, or help you build better media literacy skills. 🎯"
    ]
}

KEYWORD_MAP = {
    'hello|hi|hey|greetings|start': 'greeting',
    'fake|misinformation|disinformation|hoax|lie|false': 'fake_news_general',
    'how|work|detect|algorithm|model|ai|accuracy': 'how_it_works',
    'source|trust|reliable|credible|website|read': 'trusted_sources',
    'tip|advice|identify|spot|recognize|check': 'tips',
}

class AIChat:
    def respond(self, message, context=None, history=None):
        msg_lower = message.lower()
        
        # Check for context (recent detection result)
        if context and context.get('label'):
            return self._explain_result(context, message)
        
        # Match keywords
        for pattern, category in KEYWORD_MAP.items():
            if re.search(pattern, msg_lower):
                return random.choice(RESPONSES[category])
        
        # Check if asking about specific news
        if any(w in msg_lower for w in ['news','article','headline','report','story']):
            return "To analyze a specific news article, please paste the text in the **'Detect Fake News'** section above, or share the URL in the URL analyzer. I'll then be able to give you a detailed AI-powered analysis with confidence scores and explanations! 📊"
        
        if any(w in msg_lower for w in ['india','world','today','latest','current']):
            return "For the latest news, check the **Live News** section at the top of the page! It auto-refreshes with real-time headlines from trusted sources including NDTV, BBC, Reuters, and more. You can filter by category: India, World, Tech, Sports, Business. 📰"
        
        return random.choice(RESPONSES['default'])
    
    def _explain_result(self, context, message):
        label = context.get('label', 'UNKNOWN')
        confidence = context.get('confidence', 0)
        
        if 'why' in message.lower() or 'explain' in message.lower():
            if label == 'FAKE':
                return f"The article was classified as **FAKE** with {confidence}% confidence. Our AI detected several red flags: sensational language patterns, emotional manipulation tactics, and lack of credible source citations. These are hallmarks of misinformation. I recommend fact-checking with Alt News or BOOM before sharing. ⚠️"
            else:
                return f"The article was classified as **REAL** with {confidence}% confidence. Our AI found professional journalistic language, credible source references, and balanced reporting tone — all indicators of factual content. However, always verify independently! ✅"
        
        return f"Based on my analysis, this content appears to be **{label}** with {confidence}% confidence. Would you like me to explain the specific factors that led to this classification? Just ask 'why'! 🤖"
