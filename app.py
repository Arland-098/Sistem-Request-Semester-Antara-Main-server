from flask import Flask, flash, redirect, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from database import init_db
from routes import register_blueprints
from routes.decorators import ROLE_LABELS, get_logged_in_user, normalize_role
from services import PARTNER_BANKS, get_config

PUBLIC_ENDPOINTS = {'auth.login', 'auth.logout', 'main.health', 'static'}


def create_app(config_overrides: dict | None = None) -> Flask:
    flask_app = Flask(
        __name__,
        static_folder='public/static',
        static_url_path='/static',
        template_folder='templates',
    )
    flask_app.config.from_object(Config)
    if config_overrides:
        flask_app.config.update(config_overrides)

    # Support reverse proxies on PaaS hosting (Vercel, Render, Railway, Nginx, etc.)
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    with flask_app.app_context():
        init_db(
            db_path=flask_app.config.get('DATABASE_PATH'),
            database_url=flask_app.config.get('DATABASE_URL'),
        )

    @flask_app.before_request
    def enforce_authentication():
        if request.endpoint in PUBLIC_ENDPOINTS or request.path.startswith('/static/'):
            return None
        if not get_logged_in_user():
            session.pop('user_id', None)
            flash("Silakan login terlebih dahulu untuk mengakses sistem.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return None

    @flask_app.context_processor
    def inject_global_vars():
        user = get_logged_in_user()
        role = normalize_role(user['role']) if user else ''
        return {
            'current_user': user,
            'current_role': role,
            'current_role_label': ROLE_LABELS.get(role, role),
            'role_labels': ROLE_LABELS,
            'partner_banks': PARTNER_BANKS,
            'active_semester': get_config('active_semester', 'Semester Antara 2026/2027'),
            'reg_status': get_config('registration_status', 'Buka'),
            'proposal_start': get_config('proposal_start', '2026-06-20'),
            'proposal_end': get_config('proposal_end', '2026-06-30'),
            'reg_start': get_config('registration_start', '2026-07-01'),
            'reg_end': get_config('registration_end', '2026-07-25'),
            'payment_start': get_config('payment_start', '2026-07-26'),
            'payment_end': get_config('payment_end', '2026-08-05'),
            'sks_rate': int(get_config('sks_rate', '220000') or 220000),
            'sks_rate_kesehatan': int(get_config('sks_rate_kesehatan', '850000') or 850000),
            'max_sks': int(get_config('max_sks', '9') or 9),
            'min_quota': int(get_config('min_quota', '10') or 10),
        }

    register_blueprints(flask_app)
    return flask_app


app = create_app()


if __name__ == '__main__':
    app.run(
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False),
    )
