from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import nutrition, meal_plan

app = FastAPI(
    title="HealthAI - Service de Recommandation Nutritionnelle",
    description="Analyse de repas par IA et génération de plans nutritionnels personnalisés",
    version="1.0.0",
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
