import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.schemas import (
    MealAnalysisResponse,
    FoodItem,
    ObjectiveEnum,
    DietEnum,
    UserProfile,
)
from app.services import vision, nutrition_calc, recommender

router = APIRouter()


@router.post("/analyze", response_model=MealAnalysisResponse)
async def analyze_meal(
    image: UploadFile = File(..., description="Photo du repas (jpg, png, webp)"),
    objective: ObjectiveEnum = Form(ObjectiveEnum.maintenance),
    gender: str = Form("male"),
    diet: DietEnum = Form(DietEnum.none),
    allergies: str = Form("[]", description="JSON array des allergies ex: [\"gluten\",\"milk\"]"),
):
    """
    Analyse une photo de repas et retourne :
    - Les aliments identifiés par l'IA
    - Les valeurs nutritionnelles (calories, protéines, glucides, lipides)
    - La détection des déséquilibres
    - Des suggestions personnalisées selon l'objectif utilisateur
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (jpg, png, webp).")

    image_bytes = await image.read()

    try:
        allergies_list = json.loads(allergies)
    except json.JSONDecodeError:
        allergies_list = []

    # 1. Détection des aliments via HuggingFace
    detected_raw = vision.analyze_meal_image(image_bytes)

    # 2. Récupération des valeurs nutritionnelles (top 3 aliments détectés)
    food_items: list[FoodItem] = []
    total_calories = total_protein = total_carbs = total_fat = 0.0

    for item in detected_raw[:3]:
        nutrition = nutrition_calc.get_nutrition_for_food(item["food"])
        if nutrition:
            portion = 100.0
            cal = nutrition["calories_per_100g"] * portion / 100
            prot = nutrition["protein_per_100g"] * portion / 100
            carbs = nutrition["carbs_per_100g"] * portion / 100
            fat = nutrition["fat_per_100g"] * portion / 100

            food_items.append(
                FoodItem(
                    name=item["food"],
                    confidence=item["confidence"],
                    portion_g=portion,
                    calories=round(cal, 1),
                    protein_g=round(prot, 1),
                    carbs_g=round(carbs, 1),
                    fat_g=round(fat, 1),
                )
            )
            total_calories += cal
            total_protein += prot
            total_carbs += carbs
            total_fat += fat
        else:
            # Aliment trouvé mais pas de données nutritionnelles disponibles
            food_items.append(
                FoodItem(name=item["food"], confidence=item["confidence"])
            )

    # 3. Analyse des déséquilibres et recommandations
    user_profile = UserProfile(
        objective=objective,
        gender=gender,
        diet=diet,
        allergies=allergies_list,
    )
    balance = recommender.analyze_nutritional_balance(
        total_calories, total_protein, total_carbs, total_fat, user_profile
    )

    return MealAnalysisResponse(
        detected_foods=food_items,
        total_calories=round(total_calories, 1),
        total_protein_g=round(total_protein, 1),
        total_carbs_g=round(total_carbs, 1),
        total_fat_g=round(total_fat, 1),
        imbalances=balance["imbalances"],
        suggestions=balance["suggestions"],
        macros_ratios=balance["macros_ratios"],
    )
