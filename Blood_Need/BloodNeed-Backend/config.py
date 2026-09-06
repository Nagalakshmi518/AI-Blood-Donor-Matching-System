import os
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import quote_plus

load_dotenv()


def _parse_allowed_origins(raw_value):
    if not raw_value:
        return ["*"]
    return [item.strip() for item in raw_value.split(",") if item.strip()]


class Config:
    DEBUG = os.getenv("DEBUG", "False").strip().lower() in {
        "1", "true", "yes", "on"
    }

    DISABLE_SCHEDULER = os.getenv(
        "DISABLE_SCHEDULER", "False"
    ).strip().lower() in {
        "1", "true", "yes", "on"
    }

    SECRET_KEY = os.getenv("SECRET_KEY") or "bloodneed-local-dev-secret-change-me"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "bloodneed-local-dev-jwt-secret-change-me"

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", "1"))
    )

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    CORS_ORIGINS = _parse_allowed_origins(
        os.getenv("CORS_ORIGINS", "*")
    )

    db_user = os.getenv("DB_USER", "root")
    db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "bloodneed")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "ca.pem"
                )
            }
        }
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False