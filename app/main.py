from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import nutrition, meal_plan

app = FastAPI(
    title="HealthAI - Service de Recommandation Nutritionnelle",
    description="""
## Service de recommandation nutritionnelle — HealthAI Coach

Micro-service FastAPI exposant deux fonctionnalités principales :

### Analyse de repas (`/api/nutrition/analyze`)
- Détection des aliments via le modèle de vision **nateraw/food** (ViT, Food-101)
- Calcul des macronutriments via l'API **USDA FoodData Central**
- Détection des déséquilibres nutritionnels via un modèle **Random Forest** (scikit-learn)
- Génération de recommandations textuelles personnalisées selon l'objectif et le régime de l'utilisateur

### Plan de repas (`/api/meal-plan/generate`)
- Génération d'un plan sur 1 à 7 jours
- Filtrage automatique des allergènes et respect du régime alimentaire
- Persistance de l'historique en **MongoDB**

### Authentification
Toutes les routes nécessitent un token JWT Bearer généré par l'API principale (Express).
""",
    version="1.0.0",
    contact={
        "name": "HealthAI Coach",
    },
    license_info={
        "name": "Projet pédagogique EPSI — MSPR TPRE502",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nutrition.router, prefix="/api/nutrition", tags=["Analyse Nutritionnelle"])
app.include_router(meal_plan.router, prefix="/api/meal-plan", tags=["Plans de Repas"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "nutrition-recommendation"}


@app.get("/")
def root():
    return {
        "service": "HealthAI Nutrition Recommendation",
        "docs": "/docs",
        "health": "/health",
    }
