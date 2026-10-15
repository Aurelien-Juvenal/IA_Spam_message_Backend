from transformers import pipeline

class SpamDetector:
    def __init__(self):
        # Modèle BERT léger (environ 17 Mo), idéal pour le déploiement gratuit
        self.model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
        self.classifier = pipeline(
            "text-classification",
            model=self.model_name
        )

    def predict(self, text: str) -> dict:
        result = self.classifier(text)[0]
        # Format de sortie du modèle: LABEL_0 (HAM / Non-Spam), LABEL_1 (SPAM) ou "LABEL_1" / "LABEL_0"
        label = result["label"].upper()
        is_spam = label in ["LABEL_1", "SPAM"]
        
        return {
            "is_spam": is_spam,
            "confidence": round(result["score"], 4),
            "label_raw": label
        }