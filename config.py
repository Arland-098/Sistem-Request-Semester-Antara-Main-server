import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_db_path() -> str:
    raw_path = os.environ.get('DATABASE_PATH', '').strip()
    if not raw_path:
        return os.path.join(BASE_DIR, 'instance', 'academic.db')
    if os.path.isabs(raw_path):
        return raw_path
    return os.path.join(BASE_DIR, raw_path)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uin-semesta-semester-antara-secret-key-2026'
    DATABASE_PATH = _resolve_db_path()
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    DEBUG = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
