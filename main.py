from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from model import SpamDetector

# Dictionnaire global pour stocker le modèle chargé
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chargement du modèle au démarrage
    ml_models["spam_detector"] = SpamDetector()
    yield
    # Nettoyage à la fermeture si nécessaire
    ml_models.clear()

app = FastAPI(
    title="Spam Detection API",
    description="API REST pour la détection automatique de SMS / messages Spams.",
    version="1.0.0",
    lifespan=lifespan
)

class TextPayload(BaseModel):
    text: str = Field(..., min_length=1, example="Congratulations! You won a $1000 gift card. Call now!")

class PredictionResponse(BaseModel):
    is_spam: bool
    confidence: float
    label_raw: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Spam Detection API",
        "docs": "/docs"
    }

@app.post("/predict", response_model=PredictionResponse)
def analyze_text(payload: TextPayload):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Le texte fourni est vide.")
    
    try:
        prediction = ml_models["spam_detector"].predict(text)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {str(e)}")