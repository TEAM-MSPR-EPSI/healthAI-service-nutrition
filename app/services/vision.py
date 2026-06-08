from transformers import pipeline
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline("image-classification", model="nateraw/food", top_k=5)
    return _classifier


def analyze_meal_image(image_bytes: bytes) -> list[dict]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = get_classifier()(image)
    return [
        {"food": r["label"].replace("_", " "), "confidence": round(r["score"], 3)}
        for r in results
        if r.get("score", 0) >= 0.05
    ]