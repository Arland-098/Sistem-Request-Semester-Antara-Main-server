import secrets
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from database.seed import DEMO_ACCOUNTS_INFO
from routes.decorators import ROLE_LABELS, get_logged_in_user, normalize_role
from services import authenticate_user

auth_bp = Blueprint('auth', __name__)


def _is_safe_next_url(target: str | None) -> bool:
    if not target:
        return False
    return target.startswith('/') and not target.startswith('//')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if get_logged_in_user():
        return redirect(url_for('main.index'))

    next_url = request.args.get('next') or request.form.get('next') or ''

    if request.method == 'POST':
        identifier = request.form.get('identifier', '')
        password = request.form.get('password', '')
        user, error = authenticate_user(identifier, password)

        if error or not user:
            flash(error or "Login gagal.", "danger")
            return render_template(
                'login.html',
                demo_accounts=DEMO_ACCOUNTS_INFO,
                next_url=next_url,
                last_identifier=identifier,
            )

        session.clear()
        session['user_id'] = user['id']
        session['login_nonce'] = secrets.token_hex(8)
        session.permanent = True

        role_name = ROLE_LABELS.get(normalize_role(user['role']), user['role'])
        flash(f"Selamat datang, {user['name']} ({role_name}).", "success")

        if _is_safe_next_url(next_url):
            return redirect(next_url)
        return redirect(url_for('main.index'))

    return render_template(
        'login.html',
        demo_accounts=DEMO_ACCOUNTS_INFO,
        next_url=next_url,
        last_identifier='',
    )


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("Anda telah berhasil logout dari sistem.", "info")
    return redirect(url_for('auth.login'))
