import pickle
import os
import logging
import numpy as np
from app.models.schemas import UserProfile, ObjectiveEnum

logger = logging.getLogger(__name__)

# Même encodage que train_model.py — l'ordre doit être identique
_OBJECTIVE_ENCODING = {
    "weight_loss": 0,
    "muscle_gain": 1,
    "endurance":   2,
    "maintenance": 3,
}

# Calories journalières cibles (même source que recommender.py)
_DAILY_CALORIE_TARGETS = {
    ObjectiveEnum.weight_loss: {"male": 1800, "female": 1500},
    ObjectiveEnum.muscle_gain: {"male": 2800, "female": 2200},
    ObjectiveEnum.endurance:   {"male": 2500, "female": 2000},
    ObjectiveEnum.maintenance: {"male": 2200, "female": 1800},
}

# Recommandations textuelles par label prédit × objectif
# Clé : (label, objective) → texte personnalisé
# Si la combinaison n'existe pas, on retombe sur le texte générique (label seul)
_RECOMMENDATIONS: dict[tuple[str, str], str] = {
    # ── déficit protéines ──────────────────────────────────────────────────
    ("déficit_protéines", "weight_loss"): (
        "Protéines insuffisantes pour la perte de poids. "
        "Ajoute une source maigre : blanc de poulet, thon, œufs ou fromage blanc 0%."
    ),
    ("déficit_protéines", "muscle_gain"): (
        "Pour la prise de masse, les protéines sont prioritaires. "
        "Vise au moins 30 g par repas : steak haché, cottage cheese, whey ou légumineuses."
    ),
    ("déficit_protéines", "endurance"): (
        "Les protéines aident à la récupération musculaire. "
        "Complète avec du yaourt grec, des œufs durs ou une poignée de noix."
    ),
    ("déficit_protéines", "maintenance"): (
        "Protéines en dessous de la cible. "
        "Ajoute une portion de légumineuses, de poisson ou de produits laitiers."
    ),

    # ── excès protéines ────────────────────────────────────────────────────
    ("excès_protéines", "weight_loss"): (
        "Trop de protéines pour ce repas. "
        "Réduis légèrement la viande et enrichis l'assiette de légumes ou de glucides complexes."
    ),
    ("excès_protéines", "muscle_gain"): (
        "Légèrement au-dessus de la cible protéique, mais c'est acceptable. "
        "Assure-toi d'avoir suffisamment de glucides pour alimenter tes entraînements."
    ),
    ("excès_protéines", "endurance"): (
        "Excès de protéines au détriment des glucides. "
        "Pour l'endurance, les glucides sont ton carburant principal : ajoute du riz ou des pâtes complètes."
    ),
    ("excès_protéines", "maintenance"): (
        "Légère surconsommation de protéines. "
        "Varie les sources d'énergie : plus de légumes et de céréales complètes."
    ),

    # ── déficit glucides ───────────────────────────────────────────────────
    ("déficit_glucides", "weight_loss"): (
        "Glucides en dessous de la cible. Même en perte de poids, ton cerveau en a besoin. "
        "Opte pour des glucides à faible index glycémique : lentilles, patate douce, flocons d'avoine."
    ),
    ("déficit_glucides", "muscle_gain"): (
        "Sans glucides suffisants, ton corps va puiser dans les protéines pour l'énergie. "
        "Ajoute du riz complet, des pâtes ou des pommes de terre à ton repas."
    ),
    ("déficit_glucides", "endurance"): (
        "Déficit glucidique critique pour l'endurance. "
        "Les glucides sont ton principal carburant. Augmente les féculents : riz, pâtes, pain complet."
    ),
    ("déficit_glucides", "maintenance"): (
        "Glucides insuffisants pour l'équilibre. "
        "Inclus une portion de céréales complètes ou de légumineuses."
    ),

    # ── excès glucides ─────────────────────────────────────────────────────
    ("excès_glucides", "weight_loss"): (
        "Trop de glucides pour ton objectif de perte de poids. "
        "Remplace une partie des féculents par des légumes verts ou des protéines maigres."
    ),
    ("excès_glucides", "muscle_gain"): (
        "Légèrement au-dessus de la cible glucidique. "
        "Assure-toi que les glucides viennent de sources complexes (riz, patate douce) et non de sucres rapides."
    ),
    ("excès_glucides", "endurance"): (
        "Les glucides sont élevés, ce qui est tolérable pour l'endurance. "
        "Vérifie qu'ils proviennent de sources à index glycémique modéré pour éviter les pics d'énergie."
    ),
    ("excès_glucides", "maintenance"): (
        "Excès de glucides détecté. "
        "Réduis les portions de féculents et augmente les légumes fibreux."
    ),

    # ── excès lipides ──────────────────────────────────────────────────────
    ("excès_lipides", "weight_loss"): (
        "Trop de graisses dans ce repas, ce qui augmente significativement les calories. "
        "Préfère les cuissons vapeur ou grillées, et limite les sauces et fromages."
    ),
    ("excès_lipides", "muscle_gain"): (
        "Les lipides sont un peu élevés. "
        "Privilégie les graisses de qualité (huile d'olive, avocat, saumon) et réduis les graisses saturées."
    ),
    ("excès_lipides", "endurance"): (
        "Excès de lipides qui alourdit la digestion avant l'effort. "
        "Réserve les repas gras pour après l'entraînement."
    ),
    ("excès_lipides", "maintenance"): (
        "Lipides au-dessus de la cible. "
        "Favorise les graisses insaturées (huile d'olive, noix, poisson) et limite le beurre et la charcuterie."
    ),

    # ── équilibré ──────────────────────────────────────────────────────────
    ("équilibré", "weight_loss"): (
        "Excellent équilibre nutritionnel pour la perte de poids ! "
        "Continue sur cette lancée : des protéines maigres, peu de glucides raffinés et des graisses saines."
    ),
    ("équilibré", "muscle_gain"): (
        "Repas bien équilibré pour la prise de masse. "
        "Maintiens cet apport en protéines et glucides pour soutenir tes entraînements et ta récupération."
    ),
    ("équilibré", "endurance"): (
        "Repas parfaitement adapté à l'endurance. "
        "Les glucides te fourniront l'énergie nécessaire et les protéines optimiseront ta récupération."
    ),
    ("équilibré", "maintenance"): (
        "Repas équilibré, bravo ! "
        "Varie les aliments chaque semaine pour couvrir tous les micronutriments."
    ),
}

# Textes génériques si la combinaison label×objectif n'est pas dans le dict
_GENERIC_RECOMMENDATIONS: dict[str, str] = {
    "déficit_protéines": "Protéines insuffisantes. Ajoute une source de protéines (viande, poisson, légumineuses, œufs).",
    "excès_protéines":   "Excès de protéines. Réduis la viande et augmente les légumes ou glucides complexes.",
    "déficit_glucides":  "Glucides insuffisants. Ajoute des féculents complexes : riz, patate douce, flocons d'avoine.",
    "excès_glucides":    "Excès de glucides. Réduis les féculents et augmente les légumes fibreux.",
    "excès_lipides":     "Trop de graisses. Préfère les cuissons légères et limite les sauces grasses.",
    "équilibré":         "Repas bien équilibré ! Continue ainsi.",
}

_model_cache: dict | None = None


def _load_model() -> dict:
    """Charge model.pkl une seule fois et le met en cache (lazy loading)."""
    global _model_cache
    if _model_cache is None:
        model_path = os.path.join(os.path.dirname(__file__), "../../ml/model.pkl")
        model_path = os.path.normpath(model_path)
        with open(model_path, "rb") as f:
            _model_cache = pickle.load(f)
        logger.info("Modèle ML chargé depuis %s", model_path)
    return _model_cache


def predict_and_recommend(
    total_calories: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    user_profile: UserProfile,
) -> dict:
    """
    Prédit le déséquilibre nutritionnel d'un repas via le Random Forest,
    puis génère une recommandation textuelle personnalisée.

    Retourne :
        {
            "label":          str,   # classe prédite par le modèle
            "recommendation": str,   # texte personnalisé
            "confidence":     float, # probabilité de la classe prédite (0-1)
        }
    """
    if total_calories <= 0:
        return {
            "label": "inconnu",
            "recommendation": "Impossible de calculer les macros : aucune calorie détectée.",
            "confidence": 0.0,
        }

    # ── 1. Calculer les pourcentages caloriques ────────────────────────────
    # 1g protéine = 4 kcal | 1g glucide = 4 kcal | 1g lipide = 9 kcal
    protein_pct = (protein_g * 4 / total_calories) * 100
    carbs_pct   = (carbs_g   * 4 / total_calories) * 100
    fat_pct     = (fat_g     * 9 / total_calories) * 100

    # ── 2. Encoder l'objectif en entier (même mapping que train_model.py) ──
    objective_str = user_profile.objective.value  # ex: "weight_loss"
    objective_enc = _OBJECTIVE_ENCODING.get(objective_str, 3)  # 3 = maintenance par défaut

    # ── 3. Construire le vecteur de features (même ordre que FEATURES) ─────
    features = np.array([[
        total_calories,
        protein_g,
        carbs_g,
        fat_g,
        round(protein_pct, 1),
        round(carbs_pct, 1),
        round(fat_pct, 1),
        objective_enc,
    ]])

    # ── 4. Prédire avec le Random Forest ──────────────────────────────────
    cache = _load_model()
    model = cache["model"]

    label: str = model.predict(features)[0]

    # predict_proba retourne la probabilité de chaque classe
    # on récupère la proba de la classe prédite
    proba_vector = model.predict_proba(features)[0]
    class_index  = list(model.classes_).index(label)
    confidence   = round(float(proba_vector[class_index]), 3)

    # ── 5. Générer la recommandation personnalisée ─────────────────────────
    recommendation = _RECOMMENDATIONS.get(
        (label, objective_str),
        _GENERIC_RECOMMENDATIONS.get(label, "Repas analysé."),
    )

    # Enrichissement contextuel selon le profil
    extra = _build_contextual_extras(
        total_calories, protein_g, user_profile, label
    )
    if extra:
        recommendation += " " + extra

    return {
        "label":          label,
        "recommendation": recommendation,
        "confidence":     confidence,
    }


def _build_contextual_extras(
    total_calories: float,
    protein_g: float,
    user_profile: UserProfile,
    label: str,
) -> str:
    """Ajoute des précisions basées sur le profil (calories, allergies, régime)."""
    extras = []

    # Calories par rapport à l'objectif journalier
    target = _DAILY_CALORIE_TARGETS.get(
        user_profile.objective,
        _DAILY_CALORIE_TARGETS[ObjectiveEnum.maintenance],
    ).get(user_profile.gender, 2000)

    meal_share = (total_calories / target) * 100
    if meal_share > 45:
        extras.append(
            f"Ce repas représente {meal_share:.0f}% de ton objectif journalier ({target} kcal)."
        )

    # Rappel protéines pour prise de masse
    if user_profile.objective == ObjectiveEnum.muscle_gain and protein_g < 25 and label != "excès_protéines":
        extras.append("Pour la prise de masse, vise 25–35 g de protéines par repas.")

    # Mention régime alimentaire
    diet_val = user_profile.diet.value
    if diet_val == "vegan" and label in ("déficit_protéines",):
        extras.append("En régime vegan, combine légumineuses + céréales pour un apport complet en acides aminés.")
    elif diet_val == "vegetarian" and label in ("déficit_protéines",):
        extras.append("En végétarien, les œufs, le fromage et les légumineuses couvrent bien les besoins protéiques.")

    return " ".join(extras)