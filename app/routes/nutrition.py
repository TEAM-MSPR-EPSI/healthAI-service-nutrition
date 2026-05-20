from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.schemas import MealAnalysisResponse, FoodItem, UserProfile
from app.services import vision, nutrition_calc, recommender
from app.middleware.auth import get_current_user
from app.db.postgres import get_user_full_profile

router = APIRouter()


@router.post("/analyze", response_model=MealAnalysisResponse)
async def analyze_meal(
    image: UploadFile = File(..., description="Photo du repas (jpg, png, webp)"),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyse une photo de repas pour l'utilisateur connecté.
    Son profil santé et ses allergies sont récupérés automatiquement depuis PostgreSQL.
    Retourne les aliments détectés, les valeurs nutritionnelles et les recommandations personnalisées.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image (jpg, png, webp).")

    # Récupération du profil réel depuis PostgreSQL
    profile_data = get_user_full_profile(current_user["id"])
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profil utilisateur introuvable en base de données.")

    user_profile = UserProfile(
        objective=profile_data["objective"],
        gender=profile_data["gender"],
        age=profile_data["age"],
        weight_kg=profile_data["weight_kg"],
        height_cm=profile_data["height_cm"],
        diet=profile_data["diet"],
        allergies=profile_data["allergies"],
    )

    image_bytes = await image.read()

    # 1. Détection des aliments via HuggingFace
    detected_raw = vision.analyze_meal_image(image_bytes)

    # 2. Valeurs nutritionnelles pour les 3 aliments les plus probables
    food_items: list[FoodItem] = []
    total_calories = total_protein = total_carbs = total_fat = 0.0

    for item in detected_raw[:3]:
        nutrition = nutrition_calc.get_nutrition_for_food(item["food"])
        if nutrition:
            portion = 100.0
            cal  = nutrition["calories_per_100g"] * portion / 100
            prot = nutrition["protein_per_100g"]  * portion / 100
            carb = nutrition["carbs_per_100g"]    * portion / 100
            fat  = nutrition["fat_per_100g"]      * portion / 100

            food_items.append(FoodItem(
                name=item["food"],
                confidence=item["confidence"],
                portion_g=portion,
                calories=round(cal, 1),
                protein_g=round(prot, 1),
                carbs_g=round(carb, 1),
                fat_g=round(fat, 1),
            ))
            total_calories += cal
            total_protein  += prot
            total_carbs    += carb
            total_fat      += fat
        else:
            food_items.append(FoodItem(name=item["food"], confidence=item["confidence"]))

    # 3. Analyse des déséquilibres personnalisée selon le profil réel
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