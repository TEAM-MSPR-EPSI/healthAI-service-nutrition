from pymongo import MongoClient, ASCENDING, DESCENDING
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

_client = None


def get_mongo_db():
    global _client
    if _client is None:
        try:
            _client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
            _client.server_info()
            logger.info("MongoDB connecté avec succès.")
            # Index sur user_id pour accélérer les requêtes par utilisateur
            _client[settings.mongo_db].meal_plans.create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)]
            )
        except Exception as e:
            logger.error(f"Connexion MongoDB échouée : {e}")
            _client = None
    return _client[settings.mongo_db] if _client else None


def save_meal_plan(user_id: int, user_profile: dict, plan: list) -> str | None:
    """Persiste un plan de repas dans MongoDB avec référence à l'utilisateur PostgreSQL."""
    db = get_mongo_db()
    if db is None:
        logger.warning("MongoDB indisponible — plan de repas non sauvegardé.")
        return None

    doc = {
        "user_id": user_id,        # clé de jointure avec PostgreSQL
        "user_profile": user_profile,
        "plan": plan,
        "created_at": datetime.utcnow(),
    }
    result = db.meal_plans.insert_one(doc)
    return str(result.inserted_id)


def get_meal_plan_history(limit: int = 10) -> list:
    """Retourne les derniers plans générés, tous utilisateurs confondus."""
    db = get_mongo_db()
    if db is None:
        return []

    return list(
        db.meal_plans.find({}, {"_id": 0}).sort("created_at", DESCENDING).limit(limit)
    )


def get_meal_plans_by_user(user_id: int, limit: int = 10) -> list:
    """Retourne les plans de repas d'un utilisateur spécifique (lien via user_id PostgreSQL)."""
    db = get_mongo_db()
    if db is None:
        return []

    return list(
        db.meal_plans.find({"user_id": user_id}, {"_id": 0})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
