from sqlalchemy import create_engine, text
from app.config import settings
from datetime import date
import logging

logger = logging.getLogger(__name__)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = (
            f"postgresql://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        )
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine


def get_user_full_profile(user_id: int) -> dict | None:
    """
    Récupère depuis PostgreSQL :
    - Les données de base de l'utilisateur (user_)
    - Son profil santé (user_health_profile)
    - Ses allergies (user_allergy)
    Retourne un dict compatible avec UserProfile, ou None si l'utilisateur n'existe pas.
    """
    uid = int(user_id)

    engine = get_engine()
    try:
        with engine.connect() as conn:

            user_row = conn.execute(
                text("""
                    SELECT user_gender, user_weight, user_size, user_birth
                    FROM user_
                    WHERE user_id = :uid
                """),
                {"uid": uid},
            ).fetchone()

            if not user_row:
                return None

            profile_row = conn.execute(
                text("""
                    SELECT user_health_profile_objective,
                           user_health_profile_food_diet
                    FROM user_health_profile
                    WHERE user_id = :uid
                    ORDER BY user_health_profile_id DESC
                    LIMIT 1
                """),
                {"uid": uid},
            ).fetchone()

            allergy_rows = conn.execute(
                text("""
                    SELECT allergy
                    FROM user_allergy
                    WHERE user_id = :uid
                """),
                {"uid": uid},
            ).fetchall()

            # PostgreSQL renvoie les enums comme des objets — str() garantit une string pure
            gender = str(user_row[0]) if user_row[0] else "male"
            if gender not in ("male", "female"):
                gender = "male"

            # Calcul de l'âge depuis user_birth
            age = None
            if user_row[3]:
                birth: date = user_row[3]
                today = date.today()
                age = today.year - birth.year - (
                    (today.month, today.day) < (birth.month, birth.day)
                )

            # food_diet_enum PostgreSQL a plus de valeurs que DietEnum — on garde ce qui est connu
            VALID_DIETS = {"vegan", "vegetarian", "gluten_free", "pescatarian", "lactose_free", "halal", "kosher", "none"}
            raw_diet = str(profile_row[1]) if profile_row and profile_row[1] else "none"
            diet = raw_diet if raw_diet in VALID_DIETS else "none"

            raw_objective = str(profile_row[0]) if profile_row and profile_row[0] else "maintenance"

            allergies = [str(row[0]) for row in allergy_rows]
            logger.debug(f"user_id={user_id} → allergies brutes: {allergies}")

            return {
                "gender": gender,
                "weight_kg": float(user_row[1]) if user_row[1] else None,
                "height_cm": float(user_row[2]) if user_row[2] else None,
                "age": age,
                "objective": raw_objective,
                "diet": diet,
                "allergies": allergies,
            }

    except Exception as e:
        logger.error(f"Erreur PostgreSQL get_user_full_profile(user_id={user_id}): {e}")
        return None