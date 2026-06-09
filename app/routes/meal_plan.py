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

# Mots-clés par allergène — mappés sur les ingrédients des templates
_ALLERGEN_KEYWORDS: dict[str, list[str]] = {
    "gluten":   ["pain", "pâtes", "tortilla", "flocons d'avoine", "granola", "avoine", "semoule", "blé"],
    "milk":     ["yaourt", "lait", "fromage", "beurre", "crème", "whey", "parmesan", "feta", "cottage cheese", "fromage blanc"],
    "eggs":     ["œufs", "œuf"],
    "nuts":     ["noix", "amandes", "noisettes", "beurre d'amande", "cajou", "pistaches"],
    "peanuts":  ["cacahuète", "beurre de cacahuète", "arachide"],
    "fish":     ["saumon", "thon", "cabillaud", "poisson"],
}


def _meal_contains_allergen(meal: dict, allergies: list[str]) -> bool:
    foods_text = " ".join(meal.get("foods", [])).lower() + " " + meal.get("name", "").lower()
    for allergy in allergies:
        for keyword in _ALLERGEN_KEYWORDS.get(allergy.lower(), [allergy.lower()]):
            if keyword in foods_text:
                return True
    return False


# Ingrédients exclus par régime alimentaire
_DIET_EXCLUDED_KEYWORDS: dict[str, list[str]] = {
    "vegan": [
        "poulet", "bœuf", "dinde", "porc", "steak", "blanc de poulet", "cuisse de poulet",
        "saumon", "thon", "cabillaud", "poisson", "saumon fumé",
        "yaourt", "lait", "fromage", "beurre", "crème", "whey",
        "parmesan", "feta", "cottage cheese", "fromage blanc",
        "œufs", "œuf",
    ],
    "vegetarian": [
        "poulet", "bœuf", "dinde", "porc", "steak", "blanc de poulet", "cuisse de poulet",
        "saumon", "thon", "cabillaud", "poisson", "saumon fumé",
    ],
    "pescatarian": [
        "poulet", "bœuf", "dinde", "porc", "steak", "blanc de poulet", "cuisse de poulet",
    ],
    "gluten_free": [
        "pain", "pâtes", "tortilla", "flocons d'avoine", "granola", "semoule",
    ],
    "lactose_free": [
        "yaourt", "lait", "fromage", "beurre", "crème", "whey",
        "parmesan", "feta", "cottage cheese", "fromage blanc",
    ],
    "halal":  ["porc", "jambon", "bacon", "lard"],
    "kosher": ["porc", "jambon", "bacon", "lard"],
    "none":   [],
}


def _is_meal_compatible(meal: dict, diet: str) -> bool:
    excluded = _DIET_EXCLUDED_KEYWORDS.get(diet, [])
    if not excluded:
        return True
    foods_text = " ".join(meal.get("foods", [])).lower() + " " + meal.get("name", "").lower()
    return not any(kw in foods_text for kw in excluded)


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
    DietEnum.pescatarian: [
        "Varier les poissons : saumon, maquereau, sardines pour les oméga-3, cabillaud pour les protéines maigres.",
        "Les fruits de mer sont une excellente source de zinc et d'iode.",
    ],
    DietEnum.lactose_free: [
        "Remplacer les produits laitiers par des alternatives végétales enrichies en calcium (lait d'amande, soja, avoine).",
        "Le calcium peut aussi être apporté par les légumes verts, les sardines et les amandes.",
    ],
    DietEnum.halal: [
        "Vérifier que les viandes consommées sont certifiées halal.",
        "Les protéines végétales (légumineuses, tofu) sont une alternative pratique en déplacement.",
    ],
    DietEnum.kosher: [
        "Ne pas mélanger viande et produits laitiers dans le même repas.",
        "Prévoir un délai entre un repas carné et un repas lacté.",
    ],
    DietEnum.none: [],
}

_GENERAL_NOTES = [
    "Boire au moins 1,5 à 2L d'eau par jour.",
    "Varier les sources de protéines et les légumes chaque semaine.",
    "Adapter les portions à votre ressenti de satiété.",
]


@router.get("/profile")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Retourne le profil nutritionnel de l'utilisateur connecté (pour pré-remplir le formulaire)."""
    profile_data = get_user_full_profile(current_user["id"])
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profil utilisateur introuvable en base de données.")
    return profile_data


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

    # Normalise les valeurs frontend vers les enums backend
    _OBJ_MAP  = {"energy": "endurance", "health": "maintenance"}
    _DIET_MAP = {"standard": "none", "keto": "none", "mediterranean": "none"}

    objective_str = request.objective or profile_data["objective"]
    objective_str = _OBJ_MAP.get(objective_str, objective_str)

    diet_str = request.diet or profile_data["diet"]
    diet_str = _DIET_MAP.get(diet_str, diet_str)

    allergies = request.allergies if request.allergies is not None else profile_data["allergies"]

    user_profile = UserProfile(
        objective=objective_str,
        gender=profile_data["gender"],
        age=profile_data["age"],
        weight_kg=profile_data["weight_kg"],
        height_cm=profile_data["height_cm"],
        diet=diet_str,
        allergies=allergies,
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
            safe_options = [
                m for m in options
                if not _meal_contains_allergen(m, user_profile.allergies)
                and _is_meal_compatible(m, user_profile.diet.value)
            ]
            pool = safe_options if safe_options else options
            selected = pool[(day_num - 1) % len(pool)]
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
    allergy_notes = (
        [f"Allergies détectées ({', '.join(user_profile.allergies)}) : les repas contenant ces allergènes ont été exclus du plan."]
        if user_profile.allergies else []
    )
    weekly_notes = _GENERAL_NOTES + diet_notes + allergy_notes

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
