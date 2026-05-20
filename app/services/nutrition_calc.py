import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Nutrient IDs USDA FoodData Central
_NUTRIENT_ENERGY   = 1008  # Energy (kcal)
_NUTRIENT_PROTEIN  = 1003  # Protein (g)
_NUTRIENT_CARBS    = 1005  # Carbohydrate, by difference (g)
_NUTRIENT_FAT      = 1004  # Total lipid / fat (g)
_NUTRIENT_FIBER    = 1079  # Fiber, total dietary (g)

# Valeurs nutritionnelles de secours pour les catégories Food-101 (pour 100g)
_FALLBACK_NUTRITION: dict[str, dict] = {
    "apple pie":         {"calories": 237, "protein": 2.0, "carbs": 34.0, "fat": 11.0},
    "baby back ribs":    {"calories": 290, "protein": 26.0, "carbs": 0.0,  "fat": 20.0},
    "baklava":           {"calories": 428, "protein": 5.0,  "carbs": 52.0, "fat": 23.0},
    "beef carpaccio":    {"calories": 150, "protein": 20.0, "carbs": 0.0,  "fat": 8.0},
    "beef tartare":      {"calories": 160, "protein": 20.0, "carbs": 1.0,  "fat": 8.0},
    "beet salad":        {"calories": 74,  "protein": 2.0,  "carbs": 13.0, "fat": 2.0},
    "beignets":          {"calories": 392, "protein": 5.0,  "carbs": 45.0, "fat": 22.0},
    "bibimbap":          {"calories": 120, "protein": 7.0,  "carbs": 16.0, "fat": 3.0},
    "bread pudding":     {"calories": 153, "protein": 5.0,  "carbs": 25.0, "fat": 4.0},
    "breakfast burrito": {"calories": 210, "protein": 10.0, "carbs": 22.0, "fat": 10.0},
    "bruschetta":        {"calories": 195, "protein": 6.0,  "carbs": 28.0, "fat": 7.0},
    "caesar salad":      {"calories": 120, "protein": 8.0,  "carbs": 7.0,  "fat": 8.0},
    "cannoli":           {"calories": 350, "protein": 7.0,  "carbs": 38.0, "fat": 19.0},
    "caprese salad":     {"calories": 154, "protein": 9.0,  "carbs": 4.0,  "fat": 11.0},
    "carrot cake":       {"calories": 415, "protein": 4.0,  "carbs": 56.0, "fat": 21.0},
    "ceviche":           {"calories": 85,  "protein": 13.0, "carbs": 6.0,  "fat": 1.0},
    "cheesecake":        {"calories": 321, "protein": 6.0,  "carbs": 26.0, "fat": 22.0},
    "cheese plate":      {"calories": 350, "protein": 22.0, "carbs": 2.0,  "fat": 28.0},
    "chicken curry":     {"calories": 150, "protein": 12.0, "carbs": 8.0,  "fat": 8.0},
    "chicken quesadilla":{"calories": 200, "protein": 13.0, "carbs": 17.0, "fat": 9.0},
    "chicken wings":     {"calories": 290, "protein": 27.0, "carbs": 0.0,  "fat": 19.0},
    "chocolate cake":    {"calories": 371, "protein": 5.0,  "carbs": 51.0, "fat": 17.0},
    "chocolate mousse":  {"calories": 220, "protein": 4.0,  "carbs": 23.0, "fat": 13.0},
    "churros":           {"calories": 385, "protein": 5.0,  "carbs": 49.0, "fat": 19.0},
    "clam chowder":      {"calories": 75,  "protein": 4.0,  "carbs": 10.0, "fat": 2.0},
    "club sandwich":     {"calories": 230, "protein": 16.0, "carbs": 21.0, "fat": 9.0},
    "crab cakes":        {"calories": 195, "protein": 14.0, "carbs": 10.0, "fat": 11.0},
    "creme brulee":      {"calories": 280, "protein": 4.0,  "carbs": 27.0, "fat": 18.0},
    "croque madame":     {"calories": 280, "protein": 16.0, "carbs": 20.0, "fat": 15.0},
    "cup cakes":         {"calories": 395, "protein": 4.0,  "carbs": 57.0, "fat": 18.0},
    "deviled eggs":      {"calories": 175, "protein": 10.0, "carbs": 1.0,  "fat": 14.0},
    "donuts":            {"calories": 452, "protein": 5.0,  "carbs": 51.0, "fat": 25.0},
    "dumplings":         {"calories": 185, "protein": 8.0,  "carbs": 25.0, "fat": 6.0},
    "edamame":           {"calories": 122, "protein": 11.0, "carbs": 10.0, "fat": 5.0},
    "eggs benedict":     {"calories": 180, "protein": 12.0, "carbs": 12.0, "fat": 9.0},
    "escargots":         {"calories": 90,  "protein": 16.0, "carbs": 2.0,  "fat": 2.0},
    "falafel":           {"calories": 333, "protein": 13.0, "carbs": 32.0, "fat": 18.0},
    "filet mignon":      {"calories": 220, "protein": 26.0, "carbs": 0.0,  "fat": 13.0},
    "fish and chips":    {"calories": 290, "protein": 14.0, "carbs": 30.0, "fat": 13.0},
    "foie gras":         {"calories": 462, "protein": 11.0, "carbs": 5.0,  "fat": 44.0},
    "french fries":      {"calories": 312, "protein": 3.0,  "carbs": 41.0, "fat": 15.0},
    "french onion soup": {"calories": 70,  "protein": 3.0,  "carbs": 9.0,  "fat": 2.0},
    "french toast":      {"calories": 229, "protein": 8.0,  "carbs": 26.0, "fat": 10.0},
    "fried calamari":    {"calories": 250, "protein": 15.0, "carbs": 20.0, "fat": 12.0},
    "fried rice":        {"calories": 163, "protein": 3.0,  "carbs": 28.0, "fat": 4.0},
    "frozen yogurt":     {"calories": 127, "protein": 3.0,  "carbs": 23.0, "fat": 2.0},
    "garlic bread":      {"calories": 350, "protein": 8.0,  "carbs": 43.0, "fat": 16.0},
    "gnocchi":           {"calories": 130, "protein": 3.0,  "carbs": 28.0, "fat": 0.5},
    "greek salad":       {"calories": 100, "protein": 3.0,  "carbs": 9.0,  "fat": 6.0},
    "grilled cheese sandwich": {"calories": 290, "protein": 12.0, "carbs": 25.0, "fat": 16.0},
    "grilled salmon":    {"calories": 208, "protein": 28.0, "carbs": 0.0,  "fat": 10.0},
    "guacamole":         {"calories": 150, "protein": 2.0,  "carbs": 9.0,  "fat": 13.0},
    "gyoza":             {"calories": 200, "protein": 8.0,  "carbs": 22.0, "fat": 9.0},
    "hamburger":         {"calories": 250, "protein": 14.0, "carbs": 24.0, "fat": 11.0},
    "hot and sour soup": {"calories": 40,  "protein": 2.0,  "carbs": 5.0,  "fat": 1.0},
    "hot dog":           {"calories": 290, "protein": 10.0, "carbs": 24.0, "fat": 16.0},
    "huevos rancheros":  {"calories": 155, "protein": 8.0,  "carbs": 13.0, "fat": 7.0},
    "hummus":            {"calories": 166, "protein": 8.0,  "carbs": 14.0, "fat": 10.0},
    "ice cream":         {"calories": 207, "protein": 4.0,  "carbs": 24.0, "fat": 11.0},
    "lasagna":           {"calories": 135, "protein": 8.0,  "carbs": 14.0, "fat": 5.0},
    "lobster bisque":    {"calories": 90,  "protein": 4.0,  "carbs": 8.0,  "fat": 5.0},
    "lobster roll sandwich": {"calories": 220, "protein": 14.0, "carbs": 20.0, "fat": 9.0},
    "macaroni and cheese": {"calories": 164, "protein": 7.0, "carbs": 20.0, "fat": 6.0},
    "macarons":          {"calories": 401, "protein": 6.0,  "carbs": 61.0, "fat": 15.0},
    "miso soup":         {"calories": 40,  "protein": 3.0,  "carbs": 4.0,  "fat": 1.0},
    "mussels":           {"calories": 86,  "protein": 12.0, "carbs": 4.0,  "fat": 2.0},
    "nachos":            {"calories": 306, "protein": 7.0,  "carbs": 34.0, "fat": 16.0},
    "omelette":          {"calories": 154, "protein": 11.0, "carbs": 1.0,  "fat": 12.0},
    "onion rings":       {"calories": 285, "protein": 4.0,  "carbs": 33.0, "fat": 15.0},
    "oysters":           {"calories": 69,  "protein": 8.0,  "carbs": 4.0,  "fat": 2.0},
    "pad thai":          {"calories": 190, "protein": 9.0,  "carbs": 26.0, "fat": 6.0},
    "paella":            {"calories": 190, "protein": 11.0, "carbs": 23.0, "fat": 6.0},
    "pancakes":          {"calories": 227, "protein": 6.0,  "carbs": 35.0, "fat": 8.0},
    "panna cotta":       {"calories": 180, "protein": 3.0,  "carbs": 19.0, "fat": 10.0},
    "peking duck":       {"calories": 337, "protein": 19.0, "carbs": 0.0,  "fat": 29.0},
    "pho":               {"calories": 45,  "protein": 4.0,  "carbs": 5.0,  "fat": 1.0},
    "pizza":             {"calories": 266, "protein": 11.0, "carbs": 33.0, "fat": 10.0},
    "pork chop":         {"calories": 231, "protein": 26.0, "carbs": 0.0,  "fat": 14.0},
    "poutine":           {"calories": 250, "protein": 8.0,  "carbs": 29.0, "fat": 12.0},
    "prime rib":         {"calories": 267, "protein": 24.0, "carbs": 0.0,  "fat": 19.0},
    "pulled pork sandwich": {"calories": 280, "protein": 20.0, "carbs": 26.0, "fat": 10.0},
    "ramen":             {"calories": 75,  "protein": 5.0,  "carbs": 10.0, "fat": 2.0},
    "ravioli":           {"calories": 188, "protein": 7.0,  "carbs": 27.0, "fat": 6.0},
    "red velvet cake":   {"calories": 380, "protein": 4.0,  "carbs": 54.0, "fat": 17.0},
    "risotto":           {"calories": 166, "protein": 4.0,  "carbs": 28.0, "fat": 4.0},
    "samosa":            {"calories": 262, "protein": 5.0,  "carbs": 28.0, "fat": 15.0},
    "sashimi":           {"calories": 130, "protein": 20.0, "carbs": 0.0,  "fat": 5.0},
    "scallops":          {"calories": 111, "protein": 20.0, "carbs": 5.0,  "fat": 1.0},
    "seaweed salad":     {"calories": 70,  "protein": 2.0,  "carbs": 12.0, "fat": 1.0},
    "shrimp and grits":  {"calories": 180, "protein": 12.0, "carbs": 16.0, "fat": 7.0},
    "spaghetti bolognese": {"calories": 130, "protein": 8.0, "carbs": 15.0, "fat": 4.0},
    "spaghetti carbonara": {"calories": 190, "protein": 9.0, "carbs": 22.0, "fat": 8.0},
    "spring rolls":      {"calories": 160, "protein": 4.0,  "carbs": 18.0, "fat": 8.0},
    "steak":             {"calories": 242, "protein": 26.0, "carbs": 0.0,  "fat": 15.0},
    "strawberry shortcake": {"calories": 280, "protein": 4.0, "carbs": 42.0, "fat": 11.0},
    "sushi":             {"calories": 143, "protein": 6.0,  "carbs": 24.0, "fat": 3.0},
    "tacos":             {"calories": 210, "protein": 10.0, "carbs": 20.0, "fat": 10.0},
    "takoyaki":          {"calories": 200, "protein": 8.0,  "carbs": 22.0, "fat": 9.0},
    "tiramisu":          {"calories": 270, "protein": 5.0,  "carbs": 27.0, "fat": 16.0},
    "tuna tartare":      {"calories": 110, "protein": 18.0, "carbs": 2.0,  "fat": 3.0},
    "waffles":           {"calories": 291, "protein": 7.0,  "carbs": 37.0, "fat": 13.0},
}


_COOKING_METHODS = {
    "grilled", "baked", "fried", "roasted", "steamed", "boiled",
    "raw", "fresh", "smoked", "braised", "poached", "sauteed",
}


def _normalize_query(food_name: str) -> str:
    words = food_name.lower().split()
    filtered = [w for w in words if w not in _COOKING_METHODS]
    return " ".join(filtered) if filtered else food_name


def _extract_nutrient(nutrients: list, nutrient_id: int) -> float:
    for n in nutrients:
        if n.get("nutrientId") == nutrient_id:
            return float(n.get("value", 0) or 0)
    return 0.0


def _is_plausible(calories: float, fat: float) -> bool:
    # Rejette les huiles et corps gras purs (ex: salmon oil → 900 kcal, fat 100g)
    return 0 < calories <= 850 and fat <= 85


def get_nutrition_for_food(food_name: str) -> dict | None:
    # 1. USDA FoodData Central
    try:
        query = _normalize_query(food_name)
        params = {
            "query": query,
            "api_key": settings.usda_api_key,
            "pageSize": 5,
            "dataType": "Foundation,SR Legacy",
        }
        response = requests.get(USDA_SEARCH_URL, params=params, timeout=8)
        response.raise_for_status()
        foods = response.json().get("foods", [])

        for food in foods:
            nutrients = food.get("foodNutrients", [])
            calories = _extract_nutrient(nutrients, _NUTRIENT_ENERGY)
            fat      = _extract_nutrient(nutrients, _NUTRIENT_FAT)
            if _is_plausible(calories, fat):
                return {
                    "name": food_name,
                    "calories_per_100g": calories,
                    "protein_per_100g": _extract_nutrient(nutrients, _NUTRIENT_PROTEIN),
                    "carbs_per_100g":   _extract_nutrient(nutrients, _NUTRIENT_CARBS),
                    "fat_per_100g":     fat,
                    "fiber_per_100g":   _extract_nutrient(nutrients, _NUTRIENT_FIBER),
                }
    except Exception as e:
        logger.warning(f"USDA indisponible pour '{food_name}': {e}")

    # 2. Fallback local Food-101
    key = food_name.lower().strip()
    if key in _FALLBACK_NUTRITION:
        fb = _FALLBACK_NUTRITION[key]
        return {
            "name": food_name,
            "calories_per_100g": float(fb["calories"]),
            "protein_per_100g":  float(fb["protein"]),
            "carbs_per_100g":    float(fb["carbs"]),
            "fat_per_100g":      float(fb["fat"]),
            "fiber_per_100g":    0.0,
        }

    logger.warning(f"Aucune donnée nutritionnelle trouvée pour '{food_name}'")
    return None