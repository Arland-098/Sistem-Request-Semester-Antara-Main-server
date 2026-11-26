from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services import (
    approve_student_krs,
    get_dpa_applications,
    get_user_by_id,
    get_user_by_username,
    reject_student_krs,
)

dpa_bp = Blueprint('dpa', __name__)


def _resolve_dpa_id() -> int:
    user_id = session.get('user_id')
    if user_id:
        user = get_user_by_id(user_id)
        if user and user['role'] == 'dpa':
            return user['id']
    default_dpa = get_user_by_username('dpa1')
    return default_dpa['id'] if default_dpa else 5


@dpa_bp.route('/dpa')
def dashboard():
    dpa_id = _resolve_dpa_id()
    applications = get_dpa_applications(dpa_id)
    return render_template('dpa_dashboard.html', applications=applications, active_tab='dpa')


@dpa_bp.route('/dpa/approve/<int:app_id>', methods=['POST'])
def approve(app_id: int):
    approve_student_krs(app_id)
    flash(
        f"Pengajuan KRS #{app_id} berhasil DISETUJUI. Tagihan Virtual Account resmi telah diterbitkan secara otomatis.",
        "success",
    )
    return redirect(url_for('dpa.dashboard'))


@dpa_bp.route('/dpa/reject/<int:app_id>', methods=['POST'])
def reject(app_id: int):
    notes = (request.form.get('notes') or '').strip() or 'Pengajuan ditolak oleh DPA.'
    reject_student_krs(app_id, notes)
    flash(
        f"Pengajuan KRS #{app_id} telah DITOLAK dengan catatan: '{notes}'. Mahasiswa dapat melakukan perbaikan.",
        "warning",
    )
    return redirect(url_for('dpa.dashboard'))
