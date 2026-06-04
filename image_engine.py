"""
TruthLens AI — Image Analysis Engine
Detects manipulated/AI-generated images using OpenCV + heuristics.
"""
import os, re, io, base64, logging, hashlib
logger = logging.getLogger(__name__)

def analyze_image(image_bytes: bytes, filename: str = '') -> dict:
    """Analyze image for manipulation, deepfakes, AI generation."""
    result = {
        'manipulation_score': 0,
        'ai_generated_score': 0,
        'deepfake_score': 0,
        'is_suspicious': False,
        'flags': [],
        'metadata': {},
        'verdict': 'AUTHENTIC',
        'confidence': 85,
        'analysis_method': 'Heuristic + OpenCV'
    }
    try:
        import cv2
        import numpy as np
        # Decode image
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return {**result, 'error': 'Could not decode image', 'verdict': 'ERROR'}

        h, w = img.shape[:2]
        result['metadata']['dimensions'] = f'{w}x{h}'
        result['metadata']['size_kb'] = round(len(image_bytes)/1024, 1)
        result['metadata']['aspect_ratio'] = round(w/max(h,1), 2)

        # ── ELA (Error Level Analysis) approximation ──────────────────────────
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3,3), 0)
        diff = cv2.absdiff(gray, blur)
        ela_mean = float(np.mean(diff))
        ela_std  = float(np.std(diff))
        result['metadata']['ela_mean'] = round(ela_mean, 2)
        result['metadata']['ela_std']  = round(ela_std, 2)

        if ela_mean > 18:
            result['manipulation_score'] += 30
            result['flags'].append({'type':'danger','text':'High error level analysis score — possible digital editing'})
        elif ela_mean > 12:
            result['manipulation_score'] += 15
            result['flags'].append({'type':'warning','text':'Moderate error level analysis score detected'})

        # ── Noise analysis ────────────────────────────────────────────────────
        noise = cv2.Laplacian(gray, cv2.CV_64F).var()
        result['metadata']['noise_level'] = round(float(noise), 1)
        if noise < 20:
            result['ai_generated_score'] += 25
            result['flags'].append({'type':'warning','text':'Unusually low noise level — may indicate AI generation'})
        if noise > 3000:
            result['manipulation_score'] += 20
            result['flags'].append({'type':'warning','text':'High noise level — image may have been compressed/manipulated multiple times'})

        # ── Face detection (deepfake heuristic) ──────────────────────────────
        try:
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(face_cascade_path):
                cascade = cv2.CascadeClassifier(face_cascade_path)
                faces = cascade.detectMultiScale(gray, 1.3, 5)
                n_faces = len(faces)
                result['metadata']['faces_detected'] = n_faces
                if n_faces > 0:
                    result['flags'].append({'type':'info','text':f'{n_faces} face(s) detected — deepfake analysis applicable'})
                    # For demo: faces + high ELA = higher deepfake score
                    if ela_mean > 14 and n_faces > 0:
                        result['deepfake_score'] += 20
                        result['flags'].append({'type':'warning','text':'Face(s) present with unusual image artifacts — deepfake check recommended'})
        except Exception:
            pass

        # ── Color & compression analysis ──────────────────────────────────────
        b, g, r = cv2.split(img)
        ch_std = [float(np.std(b)), float(np.std(g)), float(np.std(r))]
        result['metadata']['color_variance'] = round(sum(ch_std)/3, 1)
        if max(ch_std) - min(ch_std) > 60:
            result['manipulation_score'] += 10
            result['flags'].append({'type':'info','text':'Uneven color channel variance detected'})

        # ── Compute composite scores ──────────────────────────────────────────
        ms  = min(result['manipulation_score'], 100)
        ais = min(result['ai_generated_score'], 100)
        ds  = min(result['deepfake_score'], 100)
        composite = (ms*0.4 + ais*0.35 + ds*0.25)

        result['manipulation_score'] = ms
        result['ai_generated_score'] = ais
        result['deepfake_score'] = ds
        result['is_suspicious'] = composite > 30

        if composite > 55:
            result['verdict'] = 'SUSPICIOUS'
            result['confidence'] = round(composite)
            result['flags'].insert(0, {'type':'danger','text':'⚠️ High probability of image manipulation or AI generation'})
        elif composite > 30:
            result['verdict'] = 'UNCERTAIN'
            result['confidence'] = round(composite)
            result['flags'].insert(0, {'type':'warning','text':'Some indicators of possible manipulation detected'})
        else:
            result['verdict'] = 'AUTHENTIC'
            result['confidence'] = round(90 - composite)
            result['flags'].insert(0, {'type':'success','text':'No significant manipulation artifacts detected'})

    except ImportError:
        # OpenCV not available — basic heuristics only
        size_kb = len(image_bytes)/1024
        result['analysis_method'] = 'Basic Heuristics (OpenCV unavailable)'
        result['metadata']['size_kb'] = round(size_kb, 1)
        result['metadata']['file_type'] = filename.split('.')[-1].upper() if '.' in filename else 'Unknown'
        result['flags'].append({'type':'info','text':'Install OpenCV for full deep analysis: pip install opencv-python-headless'})
        result['verdict'] = 'UNVERIFIED'
        result['confidence'] = 50
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        result['error'] = str(e)[:100]
        result['verdict'] = 'ERROR'

    return result
