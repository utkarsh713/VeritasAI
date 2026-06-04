"""TruthLens AI v3.0 — Centralized Configuration"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY', 'dev-only-change-in-prod-2024')
    DEBUG             = os.environ.get('FLASK_ENV', 'development') != 'production'
    PORT              = int(os.environ.get('PORT', 5000))

    # AI APIs
    GEMINI_API_KEY    = os.environ.get('GEMINI_API_KEY', '')
    NEWS_API_KEY      = os.environ.get('NEWS_API_KEY', '')
    FACT_CHECK_API_KEY= os.environ.get('FACT_CHECK_API_KEY', '')

    # Firebase (frontend uses these via JS)
    FIREBASE_CONFIG   = {
        "apiKey":            os.environ.get('FIREBASE_API_KEY', ''),
        "authDomain":        os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        "projectId":         os.environ.get('FIREBASE_PROJECT_ID', ''),
        "storageBucket":     os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        "appId":             os.environ.get('FIREBASE_APP_ID', ''),
    }

    # ML
    MODEL_CACHE  = 'models/model_cache.pkl'
    DATASETS     = {'fake': 'datasets/Fake.csv', 'true': 'datasets/True.csv'}

    # Feature flags
    @property
    def HAS_GEMINI(self):    return bool(self.GEMINI_API_KEY)
    @property
    def HAS_NEWSAPI(self):   return bool(self.NEWS_API_KEY)
    @property
    def HAS_FIREBASE(self):  return bool(self.FIREBASE_CONFIG.get('apiKey'))
    @property
    def HAS_FACTCHECK(self): return bool(self.FACT_CHECK_API_KEY)

config = Config()
