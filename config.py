"""
TruthLens AI — Configuration
All secrets loaded from environment variables / .env file
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ── Gemini AI ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY", "")

# ── News APIs ─────────────────────────────────────────────────────────────────
NEWS_API_KEY          = os.getenv("NEWS_API_KEY", "")          # newsapi.org
GOOGLE_FACTCHECK_KEY  = os.getenv("GOOGLE_FACTCHECK_KEY", "")  # factchecktools API

# ── Firebase (client-side config — safe to expose in JS) ──────────────────────
FIREBASE_CONFIG = {
    "apiKey":            os.getenv("FIREBASE_API_KEY", ""),
    "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId":         os.getenv("FIREBASE_PROJECT_ID", ""),
    "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET", ""),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
    "appId":             os.getenv("FIREBASE_APP_ID", ""),
}

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("SECRET_KEY", "dev-change-in-prod")
DEBUG        = os.getenv("FLASK_DEBUG", "false").lower() == "true"
PORT         = int(os.getenv("PORT", 5000))

# ── Rate limiting ──────────────────────────────────────────────────────────────
RATE_LIMIT_ANALYZE  = 20   # per minute per IP
RATE_LIMIT_CHAT     = 30
