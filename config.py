import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def is_vercel_runtime() -> bool:
    return bool(
        os.environ.get('VERCEL')
        or os.environ.get('VERCEL_ENV')
        or BASE_DIR.startswith('/var/task')
    )


def normalize_database_url(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    cleaned = raw_url.strip()
    if not cleaned:
        return None
    if cleaned.startswith('postgres://'):
        return 'postgresql://' + cleaned[len('postgres://'):]
    return cleaned


def _resolve_db_url() -> str | None:
    return normalize_database_url(
        os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    )


def _resolve_db_path() -> str:
    raw_path = os.environ.get('DATABASE_PATH', '').strip()
    if is_vercel_runtime():
        if raw_path and raw_path.startswith('/tmp/'):
            return raw_path
        return '/tmp/academic.db'
    if not raw_path:
        return os.path.join(BASE_DIR, 'instance', 'academic.db')
    if os.path.isabs(raw_path):
        return raw_path
    return os.path.join(BASE_DIR, raw_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uin-semesta-semester-antara-secret-key-2026'
    DATABASE_URL = _resolve_db_url()
    DATABASE_PATH = _resolve_db_path()
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    DEBUG = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')

    # Session hardening for Flask cookies (local & Vercel HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = (
        is_vercel_runtime()
        or os.environ.get('SESSION_COOKIE_SECURE', '0').lower() in ('1', 'true', 'yes')
    )
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
