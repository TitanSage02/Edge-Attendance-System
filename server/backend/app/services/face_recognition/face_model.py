import os
import requests
from pathlib import Path
from app.core.config import settings as config

def download_insightface_models():
    """Télécharge les modèles InsightFace si ils n'existent pas"""
    models_dir = Path(config.FACE_MODEL_PATH)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_url = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
    model_path = models_dir /  "buffalo_l.zip"
    
    if not model_path.exists():
        print("📥 Téléchargement du modèle InsightFace...")
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r📥 Téléchargement: {progress:.1f}%", end="", flush=True)
            
        print(f"\n✅ Modèle téléchargé: {model_path}")
        pass

if __name__ == "__main__":
    download_insightface_models()