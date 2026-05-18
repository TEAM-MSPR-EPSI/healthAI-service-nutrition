import requests
import logging

logger = logging.getLogger(__name__)

OPENFOODFACTS_URL = "https://world.openfoodfacts.org/cgi/search.pl"


def get_nutrition_for_food(food_name: str) -> dict | None:
    """Récupère les valeurs nutritionnelles depuis Open Food Facts (pour 100g)."""
    try:
        params = {
            "search_terms": food_name,
            "json": 1,
            "page_size": 1,
            "fields": "product_name,nutriments",
        }
        response = requests.get(OPENFOODFACTS_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        if not data.get("products"):
            logger.warning(f"Aucun produit trouvé pour '{food_name}'")
            return None

        nutriments = data["products"][0].get("nutriments", {})

        return {
            "name": food_name,
            "calories_per_100g": float(nutriments.get("energy-kcal_100g", 0)),
            "protein_per_100g": float(nutriments.get("proteins_100g", 0)),
            "carbs_per_100g": float(nutriments.get("carbohydrates_100g", 0)),
            "fat_per_100g": float(nutriments.get("fat_100g", 0)),
            "fiber_per_100g": float(nutriments.get("fiber_100g", 0)),
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données pour '{food_name}': {e}")
        return None


def calculate_meal_totals(food_items: list[dict]) -> dict:
    """Calcule les totaux nutritionnels pour un repas."""
    total_calories = sum(f.get("calories", 0) for f in food_items)
    total_protein = sum(f.get("protein_g", 0) for f in food_items)
    total_carbs = sum(f.get("carbs_g", 0) for f in food_items)
    total_fat = sum(f.get("fat_g", 0) for f in food_items)

    return {
        "total_calories": round(total_calories, 1),
        "total_protein_g": round(total_protein, 1),
        "total_carbs_g": round(total_carbs, 1),
        "total_fat_g": round(total_fat, 1),
    }
