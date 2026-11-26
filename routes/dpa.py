from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import roles_required
from services import approve_student_krs, get_dpa_applications, reject_student_krs

dpa_bp = Blueprint('dpa', __name__)


@dpa_bp.route('/dpa')
@roles_required('kaprodi')
def dashboard():
    applications = get_dpa_applications(dpa_id=None)
    return render_template('dpa_dashboard.html', applications=applications, active_tab='dpa')


@dpa_bp.route('/dpa/approve/<int:app_id>', methods=['POST'])
@roles_required('kaprodi')
def approve(app_id: int):
    approve_student_krs(app_id)
    flash(
        f"Pengajuan KRS #{app_id} berhasil DISETUJUI. Tagihan Virtual Account resmi telah diterbitkan secara otomatis.",
        "success",
    )
    return redirect(url_for('dpa.dashboard'))


@dpa_bp.route('/dpa/reject/<int:app_id>', methods=['POST'])
@roles_required('kaprodi')
def reject(app_id: int):
    notes = (request.form.get('notes') or '').strip() or 'Pengajuan ditolak oleh Kaprodi / Koordinator.'
    reject_student_krs(app_id, notes)
    flash(
        f"Pengajuan KRS #{app_id} telah DITOLAK dengan catatan: '{notes}'. Mahasiswa dapat melakukan perbaikan.",
        "warning",
    )
    return redirect(url_for('dpa.dashboard'))
