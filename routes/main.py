from flask import Blueprint, jsonify, render_template

from routes.decorators import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    return render_template('index.html', active_tab='home')


@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200
