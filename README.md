# HealthAI — Service de Recommandation Nutritionnelle

Micro-service Python/FastAPI du projet **HealthAI Coach** (MSPR TPRE502 — EPSI).  
Il expose une API IA capable d'analyser des photos de repas et de générer des plans nutritionnels personnalisés.

---

## Fonctionnalités

| Endpoint | Description |
|---|---|
| `POST /api/nutrition/analyze` | Analyse une photo de repas : détection des aliments, calcul des macros, recommandation ML personnalisée |
| `POST /api/meal-plan/generate` | Génère un plan de repas sur N jours selon le profil, les allergies et le régime |
| `GET /api/meal-plan/history` | Historique global des plans (admin uniquement) |
| `GET /api/meal-plan/user/{id}` | Plans d'un utilisateur spécifique |
| `GET /health` | Health check du service |
| `GET /docs` | Documentation interactive Swagger UI |

---

## Stack technique

| Composant | Technologie |
|---|---|
| Framework API | FastAPI + Uvicorn |
| Vision (détection aliments) | nateraw/food — ViT fine-tuné sur Food-101 (HuggingFace Transformers) |
| Données nutritionnelles | USDA FoodData Central API |
| Modèle ML | Random Forest (scikit-learn) — prédit le déséquilibre nutritionnel |
| Base de données profils | PostgreSQL (partagé avec l'API principale) |
| Base de données historique | MongoDB |
| Authentification | JWT Bearer (partagé avec l'API Express) |
| Conteneurisation | Docker + Docker Compose |

---

## Architecture du projet

```
healthAI-service-nutrition/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── config.py                # Variables d'environnement
│   ├── models/
│   │   └── schemas.py           # Schémas Pydantic (requêtes/réponses)
│   ├── routes/
│   │   ├── nutrition.py         # Route /analyze
│   │   └── meal_plan.py         # Routes /generate, /history, /user
│   ├── services/
│   │   ├── vision.py            # Détection aliments (nateraw/food)
│   │   ├── nutrition_calc.py    # Calcul nutritionnel (USDA)
│   │   ├── recommender.py       # Règles métier (déséquilibres)
│   │   └── ml_recommender.py    # Prédiction ML + recommandation textuelle
│   ├── db/
│   │   ├── postgres.py          # Récupération profil utilisateur
│   │   └── mongo.py             # Persistance plans de repas
│   └── middleware/
│       └── auth.py              # Validation JWT
├── ml/
│   ├── train_model.py           # Script d'entraînement du Random Forest
│   └── model.pkl                # Modèle entraîné (sérialisé)
├── docs/
│   ├── openapi.json             # Spécification OpenAPI 3.1 exportée
│   └── algorithmes_et_metriques.md  # Documentation technique complète
├── bruno/                       # Collection de requêtes Bruno (tests manuels)
├── Dockerfile
├── requirements.txt
└── .env                         # Variables d'environnement locales (non versionné)
```

---

## Prérequis

- Docker Desktop
- Le reste du projet HealthAI Coach lancé (PostgreSQL, MongoDB, API Express)

---

## Lancement

### Avec Docker Compose (recommandé)

Depuis la racine du projet global :

```bash
docker compose up -d nutrition_service
```

Le service démarre sur **http://localhost:8001**.

### Rebuild après modification du code

```bash
docker compose build nutrition_service
docker compose up -d nutrition_service
```

---

## Variables d'environnement

Créer un fichier `.env` à la racine du service (voir `.env.example`) :

```env
# PostgreSQL (profils utilisateurs)
DB_HOST=database
DB_PORT=5432
DB_NAME=myapp_db
DB_USER=postgres
DB_PASSWORD=postgres_password

# MongoDB (historique plans)
MONGO_URL=mongodb://mongodb:27017
MONGO_DB=healthai_nosql

# USDA FoodData Central
USDA_API_KEY=your_api_key_here

# JWT (doit être identique à l'API Express)
JWT_SECRET=your_jwt_secret_here

# Port du service
SERVICE_PORT=8001
```

Obtenir une clé USDA gratuite : https://fdc.nal.usda.gov/api-key-signup

---

## Modèle Machine Learning

Le Random Forest est entraîné sur un dataset synthétique de 5 000 repas générés à partir des règles métier nutritionnelles.

### Ré-entraîner le modèle

```bash
cd healthAI-service-nutrition
python ml/train_model.py
```

Le modèle est sauvegardé automatiquement dans `ml/model.pkl`.

### Performances (jeu de test — 1 000 exemples)

| Label | Précision | Rappel | F1-score |
|---|---|---|---|
| déficit_protéines | 1.00 | 1.00 | **1.00** |
| excès_protéines | 1.00 | 0.99 | **1.00** |
| déficit_glucides | 0.95 | 1.00 | **0.97** |
| déficit_glucides | 0.96 | 0.86 | **0.91** |
| équilibré | 0.88 | 0.95 | **0.91** |
| excès_lipides | 1.00 | 0.58 | **0.74** |
| **accuracy globale** | | | **0.98** |

> La classe `excès_lipides` présente un F1 plus faible (0.74) en raison de sa sous-représentation dans le dataset (1.2% des exemples). Voir `docs/algorithmes_et_metriques.md` pour l'analyse détaillée.

---

## Documentation API

- **Swagger UI (interactif)** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc
- **OpenAPI JSON** : `docs/openapi.json` ou http://localhost:8001/openapi.json

---

## Tests manuels avec Bruno

Les requêtes de test sont dans le dossier `bruno/` :

| Fichier | Description |
|---|---|
| `00-login-get-token.bru` | Login sur l'API Express, récupère le JWT |
| `01-health-check.bru` | Vérifie que le service répond |
| `02-analyze-meal.bru` | Envoie une photo de repas pour analyse |
| `04-meal-plan-history.bru` | Historique des plans (admin) |
| `05-user-meal-plans.bru` | Plans d'un utilisateur |

Importer le dossier `bruno/` dans [Bruno](https://www.usebruno.com/).

---

## Liens

- Documentation technique complète : [`docs/algorithmes_et_metriques.md`](docs/algorithmes_et_metriques.md)
- Spécification OpenAPI : [`docs/openapi.json`](docs/openapi.json)
- Documentation FastAPI : https://fastapi.tiangolo.com
- Scikit-learn : https://scikit-learn.org
- USDA FoodData Central : https://fdc.nal.usda.gov