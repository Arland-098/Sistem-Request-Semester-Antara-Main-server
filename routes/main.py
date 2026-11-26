from flask import Blueprint, flash, jsonify, redirect, render_template, session, url_for

from services import get_user_by_username

main_bp = Blueprint('main', __name__)

ROLE_USERNAMES = {
    'mahasiswa': '1251420125',
    'dpa': 'dpa1',
    'dosen': 'dosen1',
    'prodi': 'prodi',
    'keuangan': 'keuangan',
}

ROLE_REDIRECTS = {
    'mahasiswa': 'mahasiswa.krs',
    'dpa': 'dpa.dashboard',
    'dosen': 'dosen.dashboard',
    'prodi': 'prodi.monitoring',
    'keuangan': 'keuangan.pembayaran',
}


@main_bp.route('/')
def index():
    return render_template('index.html', active_tab='home')


@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


@main_bp.route('/switch_role/<role_name>')
def switch_role(role_name: str):
    username = ROLE_USERNAMES.get(role_name, '1251420125')
    user = get_user_by_username(username)
    if not user:
        flash("Akun peran tidak ditemukan.", "danger")
        return redirect(url_for('main.index'))

    session['user_id'] = user['id']
    flash(f"Berhasil beralih peran ke: {user['name']} ({user['role'].upper()})", "info")

    target_endpoint = ROLE_REDIRECTS.get(role_name, 'main.index')
    return redirect(url_for(target_endpoint))
