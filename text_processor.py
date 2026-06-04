"""Text preprocessing and analysis utilities"""
import re, math

SENSATIONAL_WORDS = ['shocking','explosive','bombshell','unbelievable','jaw-dropping',
    'outrageous','scandal','breaking','urgent','alert','exposed','leaked','banned',
    'miracle','secret','hidden','censored','conspiracy','hoax','fraud','lie']

class TextProcessor:
    def analyze(self, text):
        words = text.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_len = word_count / max(len(sentences), 1)
        
        # Sentiment (simple)
        positive_words = ['good','great','amazing','excellent','wonderful','positive','success','achieve','win','benefit']
        negative_words = ['bad','terrible','awful','horrible','worst','negative','fail','lose','danger','threat','crisis','attack']
        pos = sum(1 for w in words if w.lower() in positive_words)
        neg = sum(1 for w in words if w.lower() in negative_words)
        if neg > pos * 1.5:
            sentiment = 'Negative'
        elif pos > neg * 1.5:
            sentiment = 'Positive'
        else:
            sentiment = 'Neutral'
        
        # Sensationalism score
        text_lower = text.lower()
        sens_hits = sum(1 for w in SENSATIONAL_WORDS if w in text_lower)
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        exclamations = text.count('!')
        sensationalism_score = min(100, round((sens_hits * 8) + (caps_words * 3) + (exclamations * 5)))
        
        # Readability (simplified Flesch-Kincaid)
        syllables = sum(self._count_syllables(w) for w in words)
        if word_count > 0 and len(sentences) > 0:
            fk = 206.835 - 1.015*(word_count/len(sentences)) - 84.6*(syllables/word_count)
            fk = max(0, min(100, fk))
            if fk > 70: readability = 'Easy'
            elif fk > 50: readability = 'Moderate'
            else: readability = 'Complex'
        else:
            readability = 'Unknown'
        
        # Red flags
        red_flags = []
        if sens_hits > 2: red_flags.append(f'{sens_hits} sensational keywords')
        if caps_words > 3: red_flags.append(f'{caps_words} ALL CAPS words')
        if exclamations > 2: red_flags.append(f'{exclamations} exclamation marks')
        if avg_sentence_len < 5: red_flags.append('Very short sentences (clickbait style)')
        if not re.search(r'(said|according|reported|source|expert)', text_lower):
            red_flags.append('No source citations detected')
        
        return {
            'sentiment': sentiment,
            'sensationalism_score': sensationalism_score,
            'word_count': word_count,
            'readability': readability,
            'red_flags': red_flags
        }
    
    def _count_syllables(self, word):
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e') and count > 1:
            count -= 1
        return max(1, count)
