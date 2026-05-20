from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import MealPlanRequest, MealPlanResponse, DayPlan, Meal, UserProfile, ObjectiveEnum, DietEnum
from app.db.mongo import save_meal_plan, get_meal_plan_history, get_meal_plans_by_user
from app.db.postgres import get_user_full_profile
from app.middleware.auth import get_current_user, require_admin

router = APIRouter()

# Templates de repas par objectif
_MEALS = {
    ObjectiveEnum.weight_loss: {
        "breakfast": [
            {"name": "Yaourt grec aux fruits rouges", "foods": ["yaourt grec 0%", "fruits rouges", "graines de chia"], "calories": 280, "prep": 5},
            {"name": "Omelette aux épinards", "foods": ["œufs", "épinards", "tomates cerises"], "calories": 260, "prep": 10},
            {"name": "Smoothie protéiné", "foods": ["banane", "lait d'amande", "flocons d'avoine", "whey"], "calories": 310, "prep": 5},
        ],
        "lunch": [
            {"name": "Salade de poulet grillé", "foods": ["blanc de poulet", "salade verte", "concombre", "huile d'olive"], "calories": 380, "prep": 15},
            {"name": "Bowl quinoa légumes", "foods": ["quinoa", "avocat", "pois chiches", "légumes rôtis"], "calories": 420, "prep": 20},
            {"name": "Wrap dinde avocat", "foods": ["tortilla complète", "dinde fumée", "avocat", "tomate"], "calories": 390, "prep": 10},
        ],
        "dinner": [
            {"name": "Saumon vapeur et brocolis", "foods": ["saumon", "brocolis", "patate douce"], "calories": 420, "prep": 25},
            {"name": "Soupe de lentilles corail", "foods": ["lentilles corail", "carottes", "céleri", "cumin"], "calories": 320, "prep": 30},
            {"name": "Poulet rôti aux herbes", "foods": ["blanc de poulet", "courgettes", "herbes de Provence"], "calories": 350, "prep": 30},
        ],
        "snack": [
            {"name": "Pomme et amandes", "foods": ["pomme", "amandes (20g)"], "calories": 180, "prep": 0},
            {"name": "Fromage blanc et noix", "foods": ["fromage blanc 0%", "noix (15g)"], "calories": 160, "prep": 2},
        ],
    },
    ObjectiveEnum.muscle_gain: {
        "breakfast": [
            {"name": "Porridge protéiné", "foods": ["flocons d'avoine", "whey vanille", "banane", "beurre d'amande"], "calories": 540, "prep": 10},
            {"name": "Œufs brouillés et toast", "foods": ["4 œufs entiers", "pain complet", "avocat", "saumon fumé"], "calories": 590, "prep": 15},
        ],
        "lunch": [
            {"name": "Riz poulet légumes", "foods": ["riz basmati complet", "blanc de poulet", "poivrons", "huile d'olive"], "calories": 680, "prep": 25},
            {"name": "Pâtes bolognaise", "foods": ["pâtes complètes", "bœuf haché 5%", "sauce tomate maison", "parmesan"], "calories": 720, "prep": 30},
        ],
        "dinner": [
            {"name": "Steak patate douce", "foods": ["steak de bœuf", "patate douce", "haricots verts", "huile d'olive"], "calories": 700, "prep": 30},
            {"name": "Thon riz brocolis", "foods": ["thon en conserve", "riz complet", "brocolis", "citron"], "calories": 580, "prep": 20},
        ],
        "snack": [
            {"name": "Shake protéiné", "foods": ["whey", "lait entier", "banane"], "calories": 350, "prep": 3},
            {"name": "Cottage cheese et fruits", "foods": ["cottage cheese", "ananas", "miel"], "calories": 280, "prep": 3},
        ],
    },
    ObjectiveEnum.endurance: {
        "breakfast": [
            {"name": "Granola maison et lait", "foods": ["granola", "lait demi-écrémé", "baies", "miel"], "calories": 480, "prep": 5},
            {"name": "Toast complet et beurre de cacahuète", "foods": ["pain complet", "beurre de cacahuète", "banane", "miel"], "calories": 450, "prep": 5},
        ],
        "lunch": [
            {"name": "Pasta salade légumes", "foods": ["pâtes complètes", "légumes grillés", "feta", "vinaigrette"], "calories": 560, "prep": 20},
            {"name": "Sandwich pain complet", "foods": ["pain complet", "poulet", "salade", "tomate", "houmous"], "calories": 490, "prep": 10},
        ],
        "dinner": [
            {"name": "Risotto légumes", "foods": ["riz arborio", "courgettes", "champignons", "parmesan"], "calories": 520, "prep": 35},
            {"name": "Saumon riz et épinards", "foods": ["saumon", "riz complet", "épinards sautés", "citron"], "calories": 560, "prep": 25},
        ],
        "snack": [
            {"name": "Barre céréales maison", "foods": ["flocons d'avoine", "dattes", "noix", "miel"], "calories": 250, "prep": 15},
            {"name": "Banane et amandes", "foods": ["banane", "amandes (25g)"], "calories": 220, "prep": 0},
        ],
    },
    ObjectiveEnum.maintenance: {
        "breakfast": [
            {"name": "Yaourt granola et fruits", "foods": ["yaourt nature", "granola", "fruits de saison"], "calories": 380, "prep": 5},
            {"name": "Œufs sur le plat et pain", "foods": ["2 œufs", "pain complet", "avocat", "tomate"], "calories": 400, "prep": 10},
        ],
        "lunch": [
            {"name": "Salade composée complète", "foods": ["salade verte", "tomates", "thon", "œuf dur", "vinaigrette"], "calories": 450, "prep": 10},
            {"name": "Wrap légumes grillés", "foods": ["tortilla", "légumes grillés", "fromage", "houmous"], "calories": 480, "prep": 15},
        ],
        "dinner": [
            {"name": "Poulet légumes rôtis", "foods": ["cuisse de poulet", "légumes du marché", "pommes de terre"], "calories": 500, "prep": 35},
            {"name": "Poisson vapeur et quinoa", "foods": ["cabillaud", "quinoa", "haricots verts", "citron"], "calories": 460, "prep": 25},
        ],
        "snack": [
            {"name": "Fruits et fromage", "foods": ["pomme ou poire", "portion de fromage"], "calories": 200, "prep": 2},
            {"name": "Yaourt nature et miel", "foods": ["yaourt nature", "miel", "noix"], "calories": 180, "prep": 2},
        ],
    },
}

# Suggestions hebdomadaires selon le régime
_WEEKLY_NOTES = {
    DietEnum.vegan: [
        "Privilégier les protéines végétales : tofu, tempeh, légumineuses, seitan.",
        "Compléter avec de la vitamine B12 (levure nutritionnelle ou supplémentation).",
        "Combiner les légumineuses et les céréales pour un apport complet en acides aminés.",
    ],
    DietEnum.vegetarian: [
        "Les œufs et produits laitiers couvrent bien les besoins en protéines.",
        "Consommer des légumineuses 3 à 4 fois par semaine pour le fer et les fibres.",
    ],
    DietEnum.gluten_free: [
        "Remplacer le blé par du riz, quinoa, sarrasin ou millet.",
        "Vérifier systématiquement les étiquettes : certains produits contiennent du gluten caché.",
    ],
    DietEnum.none: [],
}

_GENERAL_NOTES = [
    "Boire au moins 1,5 à 2L d'eau par jour.",
    "Varier les sources de protéines et les légumes chaque semaine.",
    "Adapter les portions à votre ressenti de satiété.",
]


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    request: MealPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Génère un plan de repas pour l'utilisateur connecté.
    Son profil santé, régime et allergies sont récupérés automatiquement depuis PostgreSQL.
    """
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

    template = _MEALS.get(user_profile.objective, _MEALS[ObjectiveEnum.maintenance])
    plan: list[DayPlan] = []

    for day_num in range(1, request.days + 1):
        meals: list[Meal] = []
        total_cal = 0.0

        meal_types = ["breakfast", "lunch", "dinner"]
        if request.meals_per_day >= 4:
            meal_types.append("snack")

        for meal_type in meal_types:
            options = template.get(meal_type, [])
            if not options:
                continue
            selected = options[(day_num - 1) % len(options)]
            meal = Meal(
                name=selected["name"],
                type=meal_type,
                foods=selected["foods"],
                estimated_calories=float(selected["calories"]),
                prep_time_min=selected["prep"],
            )
            meals.append(meal)
            total_cal += selected["calories"]

        plan.append(DayPlan(day=day_num, meals=meals, total_calories=total_cal))

    save_meal_plan(current_user["id"], user_profile.model_dump(), [d.model_dump() for d in plan])

    diet_notes = _WEEKLY_NOTES.get(user_profile.diet, [])
    weekly_notes = _GENERAL_NOTES + diet_notes

    return MealPlanResponse(
        user_id=current_user["id"],
        user_profile=user_profile,
        plan=plan,
        weekly_notes=weekly_notes,
    )


@router.get("/history")
async def get_history(
    limit: int = 10,
    _: dict = Depends(require_admin),
):
    """Historique global de tous les plans générés. Réservé aux admins."""
    return get_meal_plan_history(limit=limit)


@router.get("/user/{user_id}")
async def get_user_plans(
    user_id: int,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Retourne les plans de repas d'un utilisateur.
    Un utilisateur ne peut consulter que ses propres plans.
    """
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé : vous ne pouvez consulter que vos propres plans.")
    return get_meal_plans_by_user(user_id=user_id, limit=limit)
