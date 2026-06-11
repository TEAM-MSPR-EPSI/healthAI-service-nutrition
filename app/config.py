import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    db_host: str = os.getenv("DB_HOST", "database")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "myapp_db")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres_password")

    mongo_url: str = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
    mongo_db: str = os.getenv("MONGO_DB", "healthai_nutrition")

    usda_api_key: str = os.getenv("USDA_API_KEY", "DEMO_KEY")

    jwt_secret: str = os.getenv("JWT_SECRET", "")

    service_port: int = int(os.getenv("SERVICE_PORT", "8001"))


settings = Settings()
