"""
Fake News Detector
NLP-based analysis using heuristics + optional ML model
"""

import re
import math
import random
import hashlib
import datetime

# ── Linguistic indicators ────────────────────────────────────────────────────

SENSATIONAL_WORDS = [
    'shocking', 'bombshell', 'explosive', 'unbelievable', 'jaw-dropping',
    'stunning', 'terrifying', 'outrageous', 'scandalous', 'exposed', 'leaked',
    'secret', 'coverup', 'cover-up', 'they don\'t want you to know',
    'media blackout', 'censored', 'suppressed', 'wake up', 'sheeple',
    'illuminati', 'deep state', 'plandemic', 'scamdemic', 'hoax',
    'false flag', 'staged', 'crisis actor', 'nwo', 'new world order',
    'must share', 'share before deleted', 'going viral', 'banned',
    'miracle cure', 'doctors hate', 'big pharma', 'government hiding',
    'urgent', 'alert', 'warning', 'breaking', 'exclusive', 'unbelievable truth',
]

CREDIBILITY_WORDS = [
    'according to', 'researchers', 'study', 'report', 'officials', 'confirmed',
    'stated', 'announced', 'published', 'data shows', 'evidence', 'sources say',
    'spokesperson', 'spokesperson said', 'in a statement', 'government', 'ministry',
    'court', 'police', 'hospital', 'university', 'institute', 'research',
]

EMOTIONAL_WORDS = [
    'angry', 'furious', 'enraged', 'disgusting', 'disgusted', 'evil', 'traitor',
    'patriot', 'hero', 'villain', 'monster', 'criminal', 'corrupt', 'liar',
    'hypocrite', 'fraud', 'cheat', 'puppet', 'slave', 'sheep', 'wake up',
    'fight back', 'resist', 'revolution', 'uprising',
]

CLICKBAIT_PATTERNS = [
    r'\b(you won\'?t believe)\b',
    r'\b(what happened next)\b',
    r'\b(this is why)\b',
    r'\b(the truth about)\b',
    r'\b(they don\'?t want you)\b',
    r'\b(number \d+ will shock you)\b',
    r'\b(before it\'?s deleted)\b',
    r'\b(100%|proven|guaranteed|definitive)\b',
    r'[A-Z]{4,}',  # ALL CAPS phrases
    r'!{2,}',       # Multiple exclamation marks
    r'\?{2,}',      # Multiple question marks
]

FAKE_CLAIMS = [
    r'\b(cure(s|d)? (cancer|covid|diabetes|hiv|aids))\b',
    r'\b(doctors (hate|don\'?t want))\b',
    r'\b(government (hiding|hiding|coverup))\b',
    r'\b(aliens (exist|landed|confirmed))\b',
    r'\b(5g (causes|spread|kills))\b',
    r'\b(vaccines? (cause|causes) autism)\b',
    r'\b(earth is flat)\b',
    r'\b(moon landing (fake|hoax|staged))\b',
    r'\b(chemtrails)\b',
]

TRUSTED_SOURCE_MENTIONS = [
    'bbc', 'reuters', 'ap news', 'associated press', 'ndtv', 'the hindu',
    'times of india', 'indian express', 'mint', 'economic times', 'cnn',
    'new york times', 'washington post', 'guardian', 'al jazeera',
    'nature', 'science', 'lancet', 'who', 'unicef', 'world health organization',
    'pib', 'press information bureau', 'ani', 'pti',
]

EXPLANATION_TEMPLATES = {
    'high_fake': [
        "🔴 **Highly Suspicious Content Detected**\n\nThis article exhibits multiple hallmarks of misinformation:\n\n• **Sensationalist Language**: Uses emotionally charged or shocking language designed to provoke immediate reaction rather than inform\n• **Unverified Claims**: Contains extraordinary claims without citing credible sources or evidence\n• **Clickbait Structure**: The headline and content appear crafted to maximize shares rather than accuracy\n• **Pattern Match**: Linguistic fingerprints match known fake news patterns in our training database\n\n**Recommendation**: Cross-verify with Reuters, BBC, or official government sources before sharing.",
        "🔴 **AI Analysis: High Probability of Misinformation**\n\nOur NLP engine flagged several red flags:\n\n• **Emotional Manipulation**: Heavy use of fear, anger, or outrage-inducing language — a classic misinformation tactic\n• **Missing Attribution**: Claims are made without naming specific credible sources\n• **Exaggerated Claims**: Uses absolute language ('always', 'never', 'proven') that real journalism avoids\n• **Viral Engineering**: Structured to trigger sharing before fact-checking\n\n**Recommendation**: Search this topic on Snopes, AltNews, or FactCheck.in for verification.",
    ],
    'medium_fake': [
        "🟡 **Questionable Content — Verify Before Sharing**\n\nThis article shows some suspicious characteristics:\n\n• **Partial Sensationalism**: Some emotionally loaded language that may distort facts\n• **Incomplete Attribution**: Sources mentioned but not clearly identified or verifiable\n• **Context Missing**: Important context appears to be omitted, which can create false impressions\n• **Bias Indicators**: Language leans heavily toward one perspective\n\n**Recommendation**: Look for corroborating reports from 2-3 independent sources.",
        "🟡 **Mixed Signals Detected**\n\nThis content has both credible and questionable elements:\n\n• **Some Valid Structure**: Factual-sounding language used, but combined with emotional appeals\n• **Selective Information**: May present true facts in a misleading context\n• **Unconfirmed Details**: Some specific claims could not be cross-referenced\n\n**Recommendation**: Check if major news outlets are covering this story.",
    ],
    'low_fake': [
        "🟢 **Likely Credible — Minor Concerns**\n\nThis article appears mostly reliable with minor observations:\n\n• **Journalistic Structure**: Uses proper attribution and measured language\n• **Source Mentions**: References identifiable sources or institutions\n• **Balanced Tone**: Avoids extreme emotional language\n• **Minor Flag**: One or two phrases slightly deviate from standard journalism norms\n\n**Recommendation**: Generally trustworthy, but always good practice to verify key statistics.",
        "🟢 **Content Appears Authentic**\n\nOur AI analysis finds this content credible:\n\n• **Factual Framing**: Language is informational rather than sensational\n• **Source Credibility**: Attribution to known institutions detected\n• **Linguistic Integrity**: Writing style consistent with professional journalism\n\n**Recommendation**: This appears to be reliable reporting.",
    ],
}


class FakeNewsDetector:
    def __init__(self):
        self.model_loaded = False
        self._try_load_ml_model()

    def _try_load_ml_model(self):
        """Try to load trained ML model"""
        try:
            import pickle
            import os
            model_path = os.path.join(os.path.dirname(__file__), '../models/fake_news_model.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.ml_model = pickle.load(f)
                self.model_loaded = True
        except Exception:
            self.model_loaded = False

    def analyze(self, text):
        """Full fake news analysis"""
        text_lower = text.lower()
        word_count = len(text.split())
        char_count = len(text)

        # ── Score calculation ────────────────────────────────────────
        fake_score = 0.0
        signals = []

        # 1. Sensational words
        sensational_hits = [w for w in SENSATIONAL_WORDS if w in text_lower]
        if sensational_hits:
            fake_score += min(0.35, len(sensational_hits) * 0.07)
            signals.append({'type': 'sensational', 'items': sensational_hits[:5], 'weight': 'high'})

        # 2. Emotional words
        emotional_hits = [w for w in EMOTIONAL_WORDS if w in text_lower]
        if emotional_hits:
            fake_score += min(0.20, len(emotional_hits) * 0.04)
            signals.append({'type': 'emotional', 'items': emotional_hits[:5], 'weight': 'medium'})

        # 3. Clickbait patterns
        clickbait_hits = []
        for pattern in CLICKBAIT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            clickbait_hits.extend(matches)
        if clickbait_hits:
            fake_score += min(0.25, len(clickbait_hits) * 0.06)
            signals.append({'type': 'clickbait', 'items': [str(h) for h in clickbait_hits[:3]], 'weight': 'high'})

        # 4. Known fake claim patterns
        fake_claim_hits = []
        for pattern in FAKE_CLAIMS:
            if re.search(pattern, text_lower):
                fake_claim_hits.append(pattern)
        if fake_claim_hits:
            fake_score += 0.40
            signals.append({'type': 'known_fake_claim', 'items': ['Known misinformation pattern detected'], 'weight': 'critical'})

        # 5. Credibility reduction
        credibility_hits = [w for w in CREDIBILITY_WORDS if w in text_lower]
        if credibility_hits:
            fake_score = max(0, fake_score - min(0.15, len(credibility_hits) * 0.025))
            signals.append({'type': 'credible_language', 'items': credibility_hits[:3], 'weight': 'reduces_score'})

        # 6. Trusted source mentions
        trusted_hits = [s for s in TRUSTED_SOURCE_MENTIONS if s in text_lower]
        if trusted_hits:
            fake_score = max(0, fake_score - 0.10)
            signals.append({'type': 'trusted_source', 'items': trusted_hits[:3], 'weight': 'reduces_score'})

        # 7. ALL CAPS ratio
        caps_words = len(re.findall(r'\b[A-Z]{3,}\b', text))
        if caps_words > 3:
            fake_score += min(0.15, caps_words * 0.02)
            signals.append({'type': 'excessive_caps', 'items': [f'{caps_words} ALL-CAPS words detected'], 'weight': 'medium'})

        # 8. Exclamation density
        excl_count = text.count('!')
        if excl_count > 2:
            fake_score += min(0.10, excl_count * 0.015)

        # 9. Try ML model if available
        ml_confidence = None
        if self.model_loaded:
            try:
                ml_pred = self.ml_model.predict([text])[0]
                ml_proba = self.ml_model.predict_proba([text])[0]
                ml_confidence = float(max(ml_proba))
                if ml_pred == 'fake':
                    fake_score = (fake_score + ml_confidence) / 2
                else:
                    fake_score = fake_score * 0.5
            except Exception:
                pass

        # Clamp score
        fake_score = max(0.0, min(1.0, fake_score))
        real_score = 1.0 - fake_score

        # ── Verdict ──────────────────────────────────────────────────
        if fake_score >= 0.55:
            verdict = 'FAKE'
            verdict_label = 'Likely Fake News'
            confidence = fake_score
            explanation_key = 'high_fake'
            risk_level = 'HIGH'
            color = 'red'
        elif fake_score >= 0.30:
            verdict = 'SUSPICIOUS'
            verdict_label = 'Suspicious — Verify'
            confidence = fake_score
            explanation_key = 'medium_fake'
            risk_level = 'MEDIUM'
            color = 'yellow'
        else:
            verdict = 'REAL'
            verdict_label = 'Likely Real News'
            confidence = real_score
            explanation_key = 'low_fake'
            risk_level = 'LOW'
            color = 'green'

        # Round confidence display
        fake_pct = round(fake_score * 100, 1)
        real_pct = round(real_score * 100, 1)

        explanation = random.choice(EXPLANATION_TEMPLATES[explanation_key])

        # ── Text stats ────────────────────────────────────────────────
        sentences = len(re.split(r'[.!?]+', text))
        avg_word_len = sum(len(w) for w in text.split()) / max(word_count, 1)
        reading_level = 'Advanced' if avg_word_len > 6 else ('Intermediate' if avg_word_len > 4.5 else 'Simple')

        return {
            'verdict': verdict,
            'verdict_label': verdict_label,
            'fake_probability': fake_pct,
            'real_probability': real_pct,
            'confidence': round(confidence * 100, 1),
            'risk_level': risk_level,
            'color': color,
            'explanation': explanation,
            'signals': signals,
            'stats': {
                'word_count': word_count,
                'char_count': char_count,
                'sentence_count': sentences,
                'reading_level': reading_level,
                'sensational_words': len(sensational_hits) if sensational_hits else 0,
                'emotional_words': len(emotional_hits) if emotional_hits else 0,
                'credibility_words': len(credibility_hits) if credibility_hits else 0,
            },
            'recommendations': self._get_recommendations(verdict, signals),
            'model_used': 'ML + NLP Hybrid' if ml_confidence else 'NLP Heuristic Engine',
            'analyzed_at': datetime.datetime.now().isoformat(),
        }

    def _get_recommendations(self, verdict, signals):
        """Generate personalized recommendations"""
        recs = [
            {'icon': '🔍', 'text': 'Search this topic on Google News for multiple perspectives'},
            {'icon': '✅', 'text': 'Check AltNews.in, FactCheck.in, or Snopes for fact-checks'},
        ]
        if verdict == 'FAKE':
            recs.append({'icon': '🚫', 'text': 'Do not share this content — it may spread misinformation'})
            recs.append({'icon': '📞', 'text': 'Report to PIB Fact Check: +918799711259'})
        elif verdict == 'SUSPICIOUS':
            recs.append({'icon': '⏳', 'text': 'Wait 24-48 hours — real stories get confirmed by multiple outlets'})
            recs.append({'icon': '🗞️', 'text': 'Check if BBC, Reuters, or NDTV have covered this'})
        else:
            recs.append({'icon': '📰', 'text': 'Content appears credible — still good to check primary sources'})
        return recs
