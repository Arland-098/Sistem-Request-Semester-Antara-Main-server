from functools import wraps
from flask import flash, g, redirect, request, session, url_for

from services import get_user_by_id

ROLE_LABELS = {
    'mahasiswa': 'Mahasiswa',
    'dosen': 'Dosen Pengampu',
    'kaprodi': 'Kaprodi / Koordinator',
    'admin_akademik': 'Admin Akademik / TU',
    'superadmin': 'Super Admin',
}

LEGACY_ROLE_ALIASES = {
    'prodi': 'kaprodi',
    'keuangan': 'admin_akademik',
    'dpa': 'dosen',
}


def normalize_role(role: str | None) -> str:
    raw = (role or '').strip().lower()
    return LEGACY_ROLE_ALIASES.get(raw, raw)


def get_logged_in_user():
    if hasattr(g, '_current_user_loaded'):
        return g._current_user

    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    if user and user['is_active'] == 0:
        user = None

    g._current_user_loaded = True
    g._current_user = user
    return user


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_logged_in_user()
        if not user:
            session.pop('user_id', None)
            flash("Silakan login terlebih dahulu untuk mengakses sistem.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return view_func(*args, **kwargs)

    return wrapper


def roles_required(*allowed_roles: str):
    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = get_logged_in_user()
            if not user:
                session.pop('user_id', None)
                flash("Silakan login terlebih dahulu untuk mengakses sistem.", "warning")
                return redirect(url_for('auth.login', next=request.path))

            user_role = normalize_role(user['role'])
            if user_role == 'superadmin' or user_role in normalized_allowed:
                return view_func(*args, **kwargs)

            role_label = ROLE_LABELS.get(user_role, user['role'])
            flash(
                f"Akses ditolak: Peran Anda ({role_label}) tidak diizinkan mengakses halaman tersebut.",
                "danger",
            )
            return redirect(url_for('main.index'))

        return wrapper

    return decorator
