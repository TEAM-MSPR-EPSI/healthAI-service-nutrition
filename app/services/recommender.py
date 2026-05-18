from app.models.schemas import UserProfile, ObjectiveEnum

# Calories journalières cibles par objectif et genre
DAILY_CALORIE_TARGETS = {
    ObjectiveEnum.weight_loss: {"male": 1800, "female": 1500},
    ObjectiveEnum.muscle_gain: {"male": 2800, "female": 2200},
    ObjectiveEnum.endurance: {"male": 2500, "female": 2000},
    ObjectiveEnum.maintenance: {"male": 2200, "female": 1800},
}

# Ratios macros cibles (en %) par objectif
MACRO_TARGETS = {
    ObjectiveEnum.weight_loss: {"protein": (25, 35), "carbs": (30, 45), "fat": (20, 35)},
    ObjectiveEnum.muscle_gain: {"protein": (25, 35), "carbs": (45, 55), "fat": (20, 30)},
    ObjectiveEnum.endurance: {"protein": (15, 25), "carbs": (50, 65), "fat": (20, 30)},
    ObjectiveEnum.maintenance: {"protein": (15, 25), "carbs": (45, 55), "fat": (25, 35)},
}


def analyze_nutritional_balance(
    total_calories: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    user_profile: UserProfile,
) -> dict:
    """Détecte les déséquilibres nutritionnels et génère des suggestions personnalisées."""

    target_calories = DAILY_CALORIE_TARGETS.get(
        user_profile.objective, DAILY_CALORIE_TARGETS[ObjectiveEnum.maintenance]
    ).get(user_profile.gender, 2000)

    imbalances = []
    suggestions = []

    if total_calories == 0:
        return {
            "target_calories": target_calories,
            "imbalances": [],
            "suggestions": ["Impossible de calculer les macros : aucune calorie détectée."],
            "macros_ratios": {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0},
        }

    protein_pct = (protein_g * 4 / total_calories) * 100
    carbs_pct = (carbs_g * 4 / total_calories) * 100
    fat_pct = (fat_g * 9 / total_calories) * 100

    targets = MACRO_TARGETS.get(user_profile.objective, MACRO_TARGETS[ObjectiveEnum.maintenance])

    if protein_pct < targets["protein"][0]:
        imbalances.append("Déficit en protéines")
        suggestions.append("Ajouter une source de protéines : poulet, œufs, légumineuses ou tofu.")
    elif protein_pct > targets["protein"][1]:
        imbalances.append("Excès de protéines")
        suggestions.append("Réduire légèrement les protéines et augmenter les glucides complexes.")

    if carbs_pct < targets["carbs"][0]:
        imbalances.append("Déficit en glucides")
        suggestions.append("Inclure des glucides complexes : riz complet, patate douce, flocons d'avoine.")
    elif carbs_pct > targets["carbs"][1]:
        imbalances.append("Excès de glucides")
        suggestions.append("Réduire les féculents raffinés et privilégier les légumes.")

    if fat_pct > targets["fat"][1]:
        imbalances.append("Excès de lipides")
        suggestions.append("Limiter les graisses saturées et favoriser les graisses insaturées (avocat, huile d'olive).")

    # Suggestion basée sur l'objectif
    if user_profile.objective == ObjectiveEnum.weight_loss and total_calories > target_calories * 0.4:
        suggestions.append(f"Ce repas représente plus de 40% de votre objectif journalier ({target_calories} kcal).")

    if user_profile.objective == ObjectiveEnum.muscle_gain and protein_g < 30:
        suggestions.append("Pour la prise de masse, visez au moins 30g de protéines par repas.")

    # Suggestion allergies
    if not imbalances:
        suggestions.append("Excellent équilibre nutritionnel pour ce repas !")

    return {
        "target_calories": target_calories,
        "imbalances": imbalances,
        "suggestions": suggestions,
        "macros_ratios": {
            "protein_pct": round(protein_pct, 1),
            "carbs_pct": round(carbs_pct, 1),
            "fat_pct": round(fat_pct, 1),
        },
    }
