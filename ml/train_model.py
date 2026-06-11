import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

# Les mêmes règles que recommender.py — c'est la "vérité terrain" pour étiqueter nos données
MACRO_TARGETS = {
    "weight_loss": {"protein": (25, 35), "carbs": (30, 45), "fat": (20, 35)},
    "muscle_gain": {"protein": (25, 35), "carbs": (45, 55), "fat": (20, 30)},
    "endurance":   {"protein": (15, 25), "carbs": (50, 65), "fat": (20, 30)},
    "maintenance": {"protein": (15, 25), "carbs": (45, 55), "fat": (25, 35)},
}

OBJECTIVES = list(MACRO_TARGETS.keys())
# On encode les objectifs en chiffres car sklearn ne comprend pas les strings
# weight_loss=0, muscle_gain=1, endurance=2, maintenance=3
OBJECTIVE_ENCODING = {obj: i for i, obj in enumerate(OBJECTIVES)}


def get_label(protein_pct: float, carbs_pct: float, fat_pct: float, objective: str) -> str:
    """
    Calcule l'étiquette (le déséquilibre principal) d'un repas.
    Mêmes règles que recommender.py — c'est notre "vérité terrain".
    """
    targets = MACRO_TARGETS[objective]

    if protein_pct < targets["protein"][0]:
        return "déficit_protéines"
    if protein_pct > targets["protein"][1]:
        return "excès_protéines"
    if carbs_pct < targets["carbs"][0]:
        return "déficit_glucides"
    if carbs_pct > targets["carbs"][1]:
        return "excès_glucides"
    if fat_pct > targets["fat"][1]:
        return "excès_lipides"
    return "équilibré"


def generate_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """
    Génère n_samples repas synthétiques avec leurs étiquettes.

    Chaque repas est défini par :
    - calories        : valeur totale du repas
    - protein/carbs/fat en grammes ET en pourcentage calorique
    - objective       : objectif de l'utilisateur (encodé en entier)
    - label           : déséquilibre détecté (la cible à prédire)
    """
    np.random.seed(42)  # Reproductibilité : même seed = même dataset à chaque exécution
    rows = []

    for _ in range(n_samples):
        calories   = np.random.uniform(200, 1200)
        objective  = np.random.choice(OBJECTIVES)

        # Générer 3 valeurs aléatoires puis les normaliser pour obtenir des %
        # Ex: [30, 50, 20] → normalisé → [30%, 50%, 20%] de l'énergie totale
        raw = np.random.uniform(5, 70, size=3)
        total = raw.sum()
        protein_pct = (raw[0] / total) * 100
        carbs_pct   = (raw[1] / total) * 100
        fat_pct     = (raw[2] / total) * 100

        # Convertir les % en grammes
        # 1g protéine = 4 kcal, 1g glucide = 4 kcal, 1g lipide = 9 kcal
        protein_g = (protein_pct / 100) * calories / 4
        carbs_g   = (carbs_pct   / 100) * calories / 4
        fat_g     = (fat_pct     / 100) * calories / 9

        label = get_label(protein_pct, carbs_pct, fat_pct, objective)

        rows.append({
            "calories":    round(calories, 1),
            "protein_g":   round(protein_g, 1),
            "carbs_g":     round(carbs_g, 1),
            "fat_g":       round(fat_g, 1),
            "protein_pct": round(protein_pct, 1),
            "carbs_pct":   round(carbs_pct, 1),
            "fat_pct":     round(fat_pct, 1),
            "objective":   OBJECTIVE_ENCODING[objective],
            "label":       label,
        })

    return pd.DataFrame(rows)


def train():
    # ── 1. Générer le dataset ──────────────────────────────────────────────
    print("Génération du dataset...")
    df = generate_dataset(5000)
    print(f"Dataset : {len(df)} exemples — répartition des labels :")
    print(df["label"].value_counts())

    # ── 2. Séparer features (X) et cible (y) ──────────────────────────────
    # X = ce que le modèle reçoit en entrée
    # y = ce qu'il doit prédire
    FEATURES = ["calories", "protein_g", "carbs_g", "fat_g",
                "protein_pct", "carbs_pct", "fat_pct", "objective"]
    X = df[FEATURES]
    y = df["label"]

    # ── 3. Train / test split ──────────────────────────────────────────────
    # test_size=0.2 → 20% pour tester, 80% pour entraîner
    # random_state=42 → reproductibilité du split
    # stratify=y → garantit que chaque label est proportionnellement
    #              représenté dans train ET test (évite un split déséquilibré)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nEntraînement : {len(X_train)} exemples")
    print(f"Test         : {len(X_test)} exemples")

    # ── 4. Entraîner le Random Forest ─────────────────────────────────────
    # n_estimators=100 → 100 arbres de décision
    # random_state=42  → reproductibilité
    print("\nEntraînement du modèle Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)  # Le modèle apprend ici
    print("Modèle entraîné.")

    # ── 5. Évaluation sur le jeu de TEST (données jamais vues) ───────────
    y_pred = model.predict(X_test)
    print("\n── Rapport de performance ──────────────────────────────────────")
    print(classification_report(y_test, y_pred))
    # classification_report affiche pour chaque label :
    #   precision : sur les repas prédits "déficit_glucides", combien étaient vrais ?
    #   recall    : sur tous les vrais "déficit_glucides", combien a-t-on détectés ?
    #   f1-score  : moyenne harmonique de precision et recall (le plus important)

    # ── 6. Sauvegarder le modèle ──────────────────────────────────────────
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": FEATURES}, f)
    print(f"\nModèle sauvegardé → {model_path}")


if __name__ == "__main__":
    train()
