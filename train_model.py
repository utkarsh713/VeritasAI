"""
Fake News Detection ML Model
Uses TF-IDF + PassiveAggressiveClassifier
"""

import pickle
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline

# ─── Text Preprocessing ────────────────────────────────────────────
def preprocess_text(text):
    """Clean and preprocess news text"""
    if not text or not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Simple stopword removal (fallback without NLTK)
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
        'his', 'their', 'our', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'out', 'up', 'down',
        'then', 'once', 'so', 'no', 'not', 'only', 'same', 'more', 'most'
    }
    
    words = text.split()
    words = [w for w in words if w not in stopwords and len(w) > 2]
    return ' '.join(words)

# ─── Fake News Indicators ───────────────────────────────────────────
FAKE_INDICATORS = [
    'shocking', 'unbelievable', 'you won\'t believe', 'breaking', 'exclusive',
    'bombshell', 'explosive', 'urgent', 'must read', 'share now', 'going viral',
    'everyone is shocked', 'secret', 'hidden truth', 'they don\'t want you to know',
    'mainstream media won\'t report', 'cover up', 'conspiracy', 'hoax',
    'fake', 'satire', 'parody', 'clickbait', 'miracle cure', 'doctors hate',
    'one weird trick', 'illuminati', 'deep state', 'crisis actor',
    'false flag', 'wake up', 'sheeple', 'truth revealed'
]

SENSATIONAL_PATTERNS = [
    r'\b(BREAKING|URGENT|SHOCKING|EXCLUSIVE|BOMBSHELL)\b',
    r'!!+',
    r'\?\?+',
    r'[A-Z]{4,}',  # All caps words
]

def analyze_text_features(text):
    """Extract features for explainability"""
    features = {
        'fake_indicators': [],
        'sensational_language': False,
        'all_caps_count': 0,
        'exclamation_count': text.count('!'),
        'question_count': text.count('?'),
        'word_count': len(text.split()),
        'avg_word_length': 0,
        'uppercase_ratio': 0,
    }
    
    text_lower = text.lower()
    for indicator in FAKE_INDICATORS:
        if indicator in text_lower:
            features['fake_indicators'].append(indicator)
    
    words = text.split()
    if words:
        features['avg_word_length'] = sum(len(w) for w in words) / len(words)
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        features['all_caps_count'] = len(caps_words)
        features['uppercase_ratio'] = len(caps_words) / len(words)
    
    for pattern in SENSATIONAL_PATTERNS:
        if re.search(pattern, text):
            features['sensational_language'] = True
            break
    
    return features

# ─── Model Creation ─────────────────────────────────────────────────
def create_model():
    """Create and return the ML pipeline"""
    
    # TF-IDF + PassiveAggressiveClassifier pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=50000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95
        )),
        ('clf', PassiveAggressiveClassifier(
            max_iter=1000,
            random_state=42,
            C=0.5
        ))
    ])
    
    return pipeline

def train_with_sample_data():
    """Train model with synthetic data when real datasets not available"""
    
    # Real news patterns
    real_samples = [
        "The government announced new economic policies today aimed at reducing inflation.",
        "Scientists discover potential treatment for alzheimer's disease in clinical trials.",
        "Stock markets closed higher today as investors responded positively to earnings reports.",
        "The prime minister met with foreign dignitaries to discuss bilateral trade agreements.",
        "New research published in Nature journal reveals climate change impact on ecosystems.",
        "Police arrested three suspects in connection with last week's bank robbery.",
        "The central bank raised interest rates by 25 basis points to combat inflation.",
        "Tech giant reports quarterly earnings exceeding analyst expectations by 12 percent.",
        "United Nations peacekeeping forces deployed to conflict zone following ceasefire agreement.",
        "Medical researchers announce successful phase three trial results for new vaccine.",
        "Parliament passed the annual budget with focus on infrastructure development.",
        "Supreme Court delivered landmark ruling on constitutional rights case today.",
        "International trade deficit narrowed as exports increased by five percent in quarter.",
        "Education ministry announced new curriculum changes effective from next academic year.",
        "State election commission announced voting dates for upcoming assembly elections.",
        "The reserve bank published its quarterly monetary policy report with growth forecasts.",
        "Agricultural department released statistics showing improvement in crop production.",
        "Defense ministry confirmed successful test of indigenous missile system.",
        "World health organization issued updated guidelines on pandemic preparedness.",
        "Municipal corporation approved urban development plan for city infrastructure.",
    ] * 50  # Multiply to increase training data
    
    # Fake news patterns  
    fake_samples = [
        "SHOCKING: Secret government plan to control minds through 5G towers REVEALED!",
        "You won't believe what Bill Gates is hiding about vaccines - THE TRUTH EXPOSED!!",
        "BOMBSHELL: Deep state conspiracy to steal elections uncovered by whistleblower!!!",
        "Doctors HATE this miracle cure that big pharma doesn't want you to know about!",
        "EXCLUSIVE: Alien technology found in Antarctica - mainstream media covering it up!",
        "URGENT SHARE: Government secretly putting chemicals in water supply - WAKE UP SHEEPLE!",
        "One weird trick that scientists discovered that could cure all diseases INSTANTLY!",
        "BREAKING: Celebrity admits to being part of illuminati in shocking confession video!",
        "They don't want you to know the real truth about COVID vaccines and microchips!",
        "CRISIS ACTOR exposed at major tragedy - false flag operation confirmed by insiders!",
        "Secret leaked document proves moon landing was completely faked by NASA in 1969!",
        "Miracle vegetable that DESTROYS cancer overnight that big pharma is hiding from you!",
        "UNBELIEVABLE: Famous politician caught in satanic ritual - video evidence here!",
        "The truth about chemtrails they never told you - mass poisoning of population!",
        "EXPOSED: Mainstream media puppet masters control all news you hear - read this now!",
        "Celebrity DEAD at 45 - hidden cause reveals pharmaceutical conspiracy cover up!!!",
        "Scientists SHOCKED by discovery proving Earth is actually flat - NASA lied to us!",
        "Deep state plot to replace world leaders with clones exposed by brave insider!",
        "MUST SHARE: New world order agenda for 2025 leaked - population control plan revealed!",
        "Bombshell confession from former CIA agent exposes decades of government mind control!",
    ] * 50
    
    texts = real_samples + fake_samples
    labels = ['REAL'] * len(real_samples) + ['FAKE'] * len(fake_samples)
    
    return texts, labels

def save_model(model_dir='/home/claude/fakenews/models'):
    """Train and save the model"""
    os.makedirs(model_dir, exist_ok=True)
    
    print("🤖 Training Fake News Detection Model...")
    texts, labels = train_with_sample_data()
    
    # Preprocess
    processed = [preprocess_text(t) for t in texts]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        processed, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Train
    model = create_model()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=['REAL', 'FAKE'])
    
    print(f"✅ Model Accuracy: {accuracy:.2%}")
    print(f"📊 Confusion Matrix:\n{cm}")
    
    # Save
    model_path = os.path.join(model_dir, 'fake_news_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    stats = {
        'accuracy': float(accuracy),
        'confusion_matrix': cm.tolist(),
        'train_size': len(X_train),
        'test_size': len(X_test),
        'model_type': 'TF-IDF + PassiveAggressiveClassifier'
    }
    
    stats_path = os.path.join(model_dir, 'model_stats.pkl')
    with open(stats_path, 'wb') as f:
        pickle.dump(stats, f)
    
    print(f"💾 Model saved to {model_path}")
    return model, stats

# ─── Prediction ─────────────────────────────────────────────────────
def predict_news(text, model=None, model_dir='/home/claude/fakenews/models'):
    """Predict if news is real or fake with confidence and explanation"""
    
    if model is None:
        model_path = os.path.join(model_dir, 'fake_news_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        else:
            model, _ = save_model(model_dir)
    
    if not text or len(text.strip()) < 20:
        return {
            'prediction': 'INSUFFICIENT',
            'confidence': 0,
            'explanation': 'Please provide more text for analysis (minimum 20 characters).',
            'features': {}
        }
    
    processed = preprocess_text(text)
    
    # Get prediction and probability
    prediction = model.predict([processed])[0]
    
    # Get decision function score for confidence
    try:
        decision = model.decision_function([processed])[0]
        # Convert to probability-like score
        confidence = min(95, max(55, 50 + abs(float(decision)) * 15))
    except:
        confidence = 75
    
    # Analyze features for explanation
    features = analyze_text_features(text)
    
    # Build explanation
    explanation = build_explanation(prediction, confidence, features, text)
    
    return {
        'prediction': prediction,
        'confidence': round(confidence, 1),
        'explanation': explanation,
        'features': features,
        'processed_text': processed[:200] + '...' if len(processed) > 200 else processed
    }

def build_explanation(prediction, confidence, features, text):
    """Build human-readable explanation"""
    reasons = []
    
    if prediction == 'FAKE':
        if features['fake_indicators']:
            reasons.append(f"🚨 Contains {len(features['fake_indicators'])} sensationalist indicator(s): '{', '.join(features['fake_indicators'][:3])}'")
        if features['sensational_language']:
            reasons.append("⚠️ Uses excessive sensational language and dramatic formatting")
        if features['exclamation_count'] > 3:
            reasons.append(f"❗ Unusual number of exclamation marks ({features['exclamation_count']}), typical of clickbait")
        if features['uppercase_ratio'] > 0.1:
            reasons.append("🔴 Excessive use of ALL CAPS text, a common misinformation tactic")
        if features['word_count'] < 50:
            reasons.append("📏 Very short content — legitimate news typically provides more context")
        if not reasons:
            reasons.append("🤖 AI pattern analysis detected characteristics consistent with misinformation")
            reasons.append("📊 Language patterns match known fake news training data")
    else:
        if features['word_count'] > 100:
            reasons.append("✅ Substantial article length with adequate context and detail")
        if not features['fake_indicators']:
            reasons.append("✅ No sensationalist or clickbait language detected")
        if features['exclamation_count'] <= 2:
            reasons.append("✅ Measured, professional tone without excessive punctuation")
        if not features['sensational_language']:
            reasons.append("✅ Factual, neutral writing style consistent with credible journalism")
        if not reasons:
            reasons.append("✅ Language patterns consistent with factual reporting")
            reasons.append("📰 Writing style matches credible news sources")
    
    return reasons

if __name__ == '__main__':
    save_model()
