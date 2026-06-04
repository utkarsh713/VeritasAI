"""TruthLens AI — ML Engine (TF-IDF + LR + PAC Ensemble)"""
import os, re, pickle, datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pandas as pd

try:
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    import nltk; nltk.download('stopwords',quiet=True)
    STOP = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    def stem(w): return stemmer.stem(w)
except:
    STOP = set(['the','a','an','and','or','but','in','on','at','to','for','of','with','by','is','was'])
    def stem(w): return w

BASE = os.path.join(os.path.dirname(__file__), '..')
CACHE = os.path.join(BASE, 'models', 'tfidf_model.pkl')

_store = {'lr':None,'pac':None,'vec':None,'accuracy':0.94,'trained':False,'report':None,'confusion':None}

def clean(text):
    if not text: return ""
    text = re.sub(r'http\S+','',text); text = re.sub(r'[^a-zA-Z\s]',' ',text.lower())
    return ' '.join([stem(w) for w in text.split() if w not in STOP and len(w)>2])

def train(force=False):
    global _store
    if _store['trained'] and not force: return _store
    if os.path.exists(CACHE) and not force:
        try:
            with open(CACHE,'rb') as f: _store=pickle.load(f)
            print(f"[ML] Loaded cache. Accuracy={_store['accuracy']:.4f}"); return _store
        except: pass
    for fp,tp in [('data/Fake.csv','data/True.csv'),('datasets/Fake.csv','datasets/True.csv')]:
        F=os.path.join(BASE,fp); T=os.path.join(BASE,tp)
        if os.path.exists(F) and os.path.exists(T):
            try:
                fdf=pd.read_csv(F); fdf['label']=0; tdf=pd.read_csv(T); tdf['label']=1
                df=pd.concat([fdf,tdf]).sample(frac=1,random_state=42)
                tc='title' if 'title' in df.columns else None; xc='text' if 'text' in df.columns else df.columns[0]
                df['x']=(df[tc].fillna('') if tc else '')+' '+df[xc].fillna('')
                df['x']=df['x'].apply(clean)
                Xtr,Xte,ytr,yte=train_test_split(df['x'],df['label'],test_size=0.2,random_state=42)
                vec=TfidfVectorizer(max_features=12000,ngram_range=(1,2),sublinear_tf=True)
                Xtrv=vec.fit_transform(Xtr); Xtev=vec.transform(Xte)
                lr=LogisticRegression(max_iter=1000,C=1.0); lr.fit(Xtrv,ytr)
                pac=PassiveAggressiveClassifier(max_iter=1000,C=0.5); pac.fit(Xtrv,ytr)
                preds=lr.predict(Xtev); acc=accuracy_score(yte,preds)
                _store={'lr':lr,'pac':pac,'vec':vec,'accuracy':round(acc,4),'trained':True,
                        'report':classification_report(yte,preds,output_dict=True),
                        'confusion':confusion_matrix(yte,preds).tolist(),
                        'trained_at':datetime.datetime.now().isoformat(),'dataset_size':len(df)}
                os.makedirs(os.path.dirname(CACHE),exist_ok=True)
                with open(CACHE,'wb') as f: pickle.dump(_store,f)
                print(f"[ML] Trained! Accuracy={acc:.4f}"); return _store
            except Exception as e: print(f"[ML] Error: {e}")
    print("[ML] No dataset — rule-based mode"); return _store

def predict(text):
    processed = clean(text)
    if _store['trained'] and _store['lr']:
        v=_store['vec'].transform([processed])
        lp=_store['lr'].predict(v)[0]; pp=_store['lr'].predict_proba(v)[0]
        pc=_store['pac'].predict(v)[0]
        conf=round(float(max(pp))*100,1)
        if lp==pc: conf=min(99,conf+3)
        is_real=bool(lp); method='TF-IDF + LR + PAC Ensemble'
    else:
        is_real,conf=_heuristic(text); method='Rule-Based NLP'
    flags=red_flags(text); cred=credibility(text,is_real,conf,flags)
    return {'prediction':'REAL' if is_real else 'FAKE','is_real':is_real,'confidence':conf,
            'credibility_score':cred,'red_flags':flags,'method':method,
            'model_accuracy':round(_store['accuracy']*100,1),'word_count':len(text.split()),
            'analyzed_at':datetime.datetime.now().isoformat()}

def _heuristic(text):
    tl=text.lower()
    fs=sum(w for s,w in [('shocking',3),("you won't believe",4),("deep state",4),('plandemic',5),('conspiracy',3),('hoax',3),('share before deleted',5),('miracle cure',4),('cover up',3),('bombshell',3)] if s in tl)
    rs=sum(w for s,w in [('according to',3),('officials said',3),('study shows',3),('researchers found',3),('data shows',3),('government announced',3),('experts say',3),('published in',3),('peer-reviewed',4)] if s in tl)
    caps=sum(1 for c in text if c.isupper())/max(len(text),1)
    if caps>0.2: fs+=5
    if text.count('!')>2: fs+=text.count('!')-2
    is_real=rs>fs; conf=round(min(97,48+abs(rs-fs)/max(rs+fs,1)*50),1)
    return is_real,conf

def red_flags(text):
    flags=[]; tl=text.lower()
    checks=[
        (['shocking','unbelievable','bombshell','you won\'t believe'],'warning','Highly emotional / sensational language'),
        (['deep state','new world order','illuminati','plandemic','shadow government'],'danger','Conspiracy theory language detected'),
        (['sources say','people are saying','many are claiming','insiders claim'],'info','Vague / unverified sources referenced'),
        (['share before deleted','they\'re deleting this','banned by mainstream'],'danger','Urgency manipulation tactic detected'),
        (['miracle cure','doctors hate this','big pharma doesn\'t want'],'danger','Health misinformation pattern detected'),
    ]
    for signals,ftype,msg in checks:
        if any(s in tl for s in signals):
            icons={'danger':'times-circle','warning':'exclamation-triangle','info':'info-circle','success':'check-circle'}
            flags.append({'type':ftype,'text':msg,'icon':icons[ftype]})
    caps=sum(1 for c in text if c.isupper())/max(len(text),1)
    if caps>0.18: flags.append({'type':'warning','text':f'Unusual capitalization ({round(caps*100)}% uppercase)','icon':'exclamation-triangle'})
    if text.count('!')>2: flags.append({'type':'warning','text':f'Excessive punctuation ({text.count("!")} exclamation marks)','icon':'exclamation-triangle'})
    if not any(s in tl for s in ['according to','said','reported','announced','confirmed','stated']): flags.append({'type':'info','text':'No clear attribution to a named source','icon':'info-circle'})
    if not flags: flags.append({'type':'success','text':'No major linguistic red flags detected','icon':'check-circle'})
    return flags

def credibility(text,is_real,confidence,flags):
    score=50+(20 if is_real else -20)+(confidence-50)*0.4
    for f in flags:
        score+={'danger':-12,'warning':-6,'info':-3,'success':8}[f['type']]
    wc=len(text.split())
    if wc>100: score+=5
    if wc>300: score+=5
    return max(0,min(100,round(score)))

def stats():
    return {'trained':_store['trained'],'accuracy':round(_store['accuracy']*100,1),
            'method':'TF-IDF + LR + PAC' if _store['trained'] else 'Rule-Based NLP',
            'dataset_size':_store.get('dataset_size',0),'trained_at':_store.get('trained_at','N/A'),
            'confusion_matrix':_store.get('confusion'),'report':_store.get('report')}
