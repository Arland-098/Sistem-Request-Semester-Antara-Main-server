from flask import Blueprint, jsonify, render_template, request

from routes.decorators import get_logged_in_user, login_required, normalize_role
from services import get_announcements, get_courses_grouped_by_semester, get_programs

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    user = get_logged_in_user()
    role = normalize_role(user['role']) if user else ''

    grouped_courses = {}
    announcements = []
    programs = []
    selected_prodi = request.args.get('prodi', '60')

    if role == 'mahasiswa':
        grouped_courses = get_courses_grouped_by_semester(prodi_code=selected_prodi)
        announcements = get_announcements(active_only=True)
        programs = get_programs(active_only=True)

    return render_template(
        'index.html',
        active_tab='home',
        grouped_courses=grouped_courses,
        announcements=announcements,
        programs=programs,
        selected_prodi=selected_prodi,
    )


@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200
