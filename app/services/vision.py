from transformers import pipeline
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        logger.info("Chargement du modèle HuggingFace (nateraw/food)...")
        # nateraw/food : ViT entraîné sur Food-101, 101 catégories alimentaires
        _classifier = pipeline(
            "image-classification",
            model="nateraw/food",
            top_k=5,
        )
        logger.info("Modèle chargé avec succès.")
    return _classifier


def analyze_meal_image(image_bytes: bytes) -> list[dict]:
    """Identifie les aliments dans une image et retourne les 5 meilleurs résultats."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    classifier = get_classifier()
    results = classifier(image)
    return [
        {"food": r["label"].replace("_", " "), "confidence": round(r["score"], 3)}
        for r in results
    ]
