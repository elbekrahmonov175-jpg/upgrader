import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Railway обычно даёт DATABASE_URL в формате postgres://...
    # SQLAlchemy 2.x требует postgresql://, поэтому конвертируем
    raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Виртуальная валюта, RTP и т.д.
    START_BALANCE = 5000
    RTP = 0.97
    MAX_CHANCE = 0.95

    # Username, который автоматически станет админом при регистрации/входе.
    # Задаётся через переменную окружения ADMIN_USERNAME в Railway.
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")

    # Тестовые инструменты (форс-результат апгрейда) — ТОЛЬКО для локальной
    # разработки. По умолчанию выключено. Не включай это на публичном
    # деплое — это чисто отладочная фича для тебя при вёрстке/тестах.
    DEBUG_TOOLS_ENABLED = os.environ.get("DEBUG_TOOLS_ENABLED", "false").lower() == "true"
