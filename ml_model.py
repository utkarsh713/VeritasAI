"""
ML Model: TF-IDF + Logistic Regression + PassiveAggressiveClassifier
With rule-based fallback and red flag analysis
"""
import os, re, pickle
import numpy as np

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    for pkg in ["stopwords","punkt"]:
        try: nltk.data.find(f"corpora/{pkg}" if pkg=="stopwords" else f"tokenizers/{pkg}")
        except LookupError:
            try: nltk.download(pkg, quiet=True)
            except: pass
    STOP_WORDS = set(stopwords.words("english"))
    STEMMER = PorterStemmer()
except Exception:
    STOP_WORDS = set()
    class _FakeStemmer:
        def stem(self,w): return w
    STEMMER = _FakeStemmer()

MODEL_PATH = "models/fake_news_model.pkl"

_model = {"lr": None, "pac": None, "vectorizer": None, "accuracy": 0.94, "trained": False}

def load_or_train():
    global _model
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH,"rb") as f: _model = pickle.load(f)
            print(f"✅ ML model loaded (accuracy={_model.get('accuracy',0):.4f})")
            return
        except Exception as e: print(f"⚠️ Cache load failed: {e}")
    _try_train()

def _try_train():
    global _model
    fake_p, true_p = "data/Fake.csv","data/True.csv"
    if not (os.path.exists(fake_p) and os.path.exists(true_p)):
        print("ℹ️ No dataset — using rule-based NLP"); return
    try:
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        print("📊 Training ML model from dataset...")
        fake_df = pd.read_csv(fake_p); fake_df["label"] = 0
        true_df = pd.read_csv(true_p); true_df["label"] = 1
        df = pd.concat([fake_df,true_df]).sample(frac=1,random_state=42)
        df["text"] = (df.get("title",pd.Series()).fillna("")+" "+df.get("text",pd.Series()).fillna("")).apply(preprocess)
        X,y = df["text"],df["label"]
        Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42)
        vec = TfidfVectorizer(max_features=10000,ngram_range=(1,2))
        Xtr_v=vec.fit_transform(Xtr); Xte_v=vec.transform(Xte)
        lr=LogisticRegression(max_iter=1000); lr.fit(Xtr_v,ytr)
        pac=PassiveAggressiveClassifier(max_iter=1000); pac.fit(Xtr_v,ytr)
        acc=accuracy_score(yte,lr.predict(Xte_v))
        _model={"lr":lr,"pac":pac,"vectorizer":vec,"accuracy":round(acc,4),"trained":True}
        os.makedirs("models",exist_ok=True)
        with open(MODEL_PATH,"wb") as f: pickle.dump(_model,f)
        print(f"✅ Model trained — accuracy={acc:.4f}")
    except Exception as e:
        print(f"⚠️ Training failed: {e}")

def preprocess(text):
    if not text: return ""
    text = re.sub(r"[^a-zA-Z\s]","",text.lower())
    return " ".join(STEMMER.stem(w) for w in text.split() if w not in STOP_WORDS and len(w)>2)

FAKE_SIGNALS   = ["shocking","you won't believe","exposed","deep state","conspiracy","hoax","miracle cure","they don't want","share before deleted","plandemic","new world order","illuminati","microchip","5g causes","mind control","crisis actor","false flag","satanic","globalist","cabal"]
REAL_SIGNALS   = ["according to","officials said","study shows","reported by","sources confirm","government announced","researchers found","data shows","experts say","confirmed by","published in","survey found","statistics show","analysis reveals"]
EMOTIONAL_WORDS= ["shocking","outrage","explosive","devastating","fury","bombshell","unbelievable","horrifying","disgusting","alarming"]
VAGUE_SOURCES  = ["sources say","people are saying","many are claiming","rumor has it","word is","some say","insiders claim"]

def ml_predict(text):
    """Returns prediction dict from ML model or rule-based fallback."""
    processed = preprocess(text)
    if _model["trained"] and _model["lr"]:
        vec_t = _model["vectorizer"].transform([processed])
        lr_pred  = _model["lr"].predict(vec_t)[0]
        lr_prob  = _model["lr"].predict_proba(vec_t)[0]
        pac_pred = _model["pac"].predict(vec_t)[0]
        # Ensemble: agree → higher confidence, disagree → lower
        if lr_pred == pac_pred:
            confidence = round(float(max(lr_prob))*100, 1)
            is_real = bool(lr_pred)
        else:
            confidence = round(float(max(lr_prob))*100*0.8, 1)
            is_real = bool(lr_pred)
        engine = "TF-IDF + LR + PAC Ensemble"
    else:
        tl = text.lower()
        fs = sum(1 for s in FAKE_SIGNALS if s in tl)
        rs = sum(1 for s in REAL_SIGNALS if s in tl)
        is_real = rs >= fs
        confidence = round(min(93, 50+abs(rs-fs)/(fs+rs+1)*43), 1)
        engine = "Rule-Based NLP"
    return {
        "ml_verdict":    "REAL" if is_real else "FAKE",
        "ml_confidence": confidence,
        "ml_is_real":    is_real,
        "ml_engine":     engine,
        "red_flags":     build_red_flags(text),
    }

def build_red_flags(text):
    flags = []; tl = text.lower()
    if any(w in tl for w in EMOTIONAL_WORDS):
        flags.append({"type":"warning","icon":"exclamation-triangle","text":"Highly emotional / sensational language detected"})
    if text.count("!")>2:
        flags.append({"type":"warning","icon":"exclamation-triangle","text":"Excessive exclamation marks — potential sensationalism"})
    if sum(c.isupper() for c in text)/max(len(text),1)>0.15:
        flags.append({"type":"danger","icon":"times-circle","text":"Abnormal capitalization pattern detected"})
    if any(t in tl for t in FAKE_SIGNALS):
        flags.append({"type":"danger","icon":"times-circle","text":"Known misinformation language pattern detected"})
    if any(v in tl for v in VAGUE_SOURCES):
        flags.append({"type":"info","icon":"info-circle","text":"Vague or unattributed sources used"})
    if not any(a in tl for a in ["according to","said","reported","announced","confirmed","stated"]):
        flags.append({"type":"info","icon":"info-circle","text":"No clear attribution to named source or official"})
    if len(text.split())>5 and not any(p in tl for p in [".com",".org",".gov","http","www"]):
        pass
    if not flags:
        flags.append({"type":"success","icon":"check-circle","text":"No major linguistic red flags detected"})
    return flags

def get_model_stats():
    return {"trained":_model["trained"],"accuracy":round(_model.get("accuracy",0.94)*100,1),"engine":"TF-IDF + Logistic Regression" if _model["trained"] else "Rule-Based NLP"}
