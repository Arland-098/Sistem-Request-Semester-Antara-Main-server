from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import roles_required
from services import (
    expire_invoice,
    get_all_invoices,
    process_expired_invoices,
    reconcile_manual_payment,
    set_config,
    sync_invoices_for_ready_applications,
)

keuangan_bp = Blueprint('keuangan', __name__, url_prefix='/keuangan')


@keuangan_bp.route('/tarif')
@roles_required('keuangan')
def tarif():
    return render_template('keuangan_tarif.html', active_tab='keuangan_tarif')


@keuangan_bp.route('/tarif/update', methods=['POST'])
@roles_required('keuangan')
def tarif_update():
    raw_reguler = request.form.get('sks_rate', '220000')
    raw_kesehatan = request.form.get('sks_rate_kesehatan', '850000')
    try:
        parsed_reguler = int(raw_reguler)
        parsed_kesehatan = int(raw_kesehatan)
    except (TypeError, ValueError):
        flash("Nominal tarif biaya per SKS harus berupa angka valid.", "danger")
        return redirect(url_for('keuangan.tarif'))

    if parsed_reguler < 0 or parsed_kesehatan < 0:
        flash("Nominal tarif biaya per SKS tidak boleh bernilai negatif.", "danger")
        return redirect(url_for('keuangan.tarif'))

    set_config('sks_rate', parsed_reguler)
    set_config('sks_rate_kesehatan', parsed_kesehatan)
    flash(
        f"Tarif biaya SKS diperbarui: Sarjana Reguler Rp{parsed_reguler:,} | Ilmu Kesehatan Rp{parsed_kesehatan:,} (SK Rektor 686/2025).",
        "success",
    )
    return redirect(url_for('keuangan.tarif'))


@keuangan_bp.route('/pembayaran')
@roles_required('keuangan')
def pembayaran():
    invoices = get_all_invoices()
    return render_template('keuangan_pembayaran.html', invoices=invoices, active_tab='keuangan_pembayaran')


@keuangan_bp.route('/sync_va', methods=['POST'])
@roles_required('keuangan')
def sync_va():
    issued_count = sync_invoices_for_ready_applications()
    if issued_count:
        flash(
            f"Berhasil menerbitkan {issued_count} tagihan Virtual Account untuk pengajuan Disetujui DPA pada kelas yang resmi dibuka (BR-08).",
            "success",
        )
    else:
        flash(
            "Tidak ada tagihan baru yang perlu diterbitkan. Pastikan pendaftaran sudah ditutup dan status kelas telah ditetapkan Dibuka / Dispensasi Buka (BR-08).",
            "info",
        )
    return redirect(url_for('keuangan.pembayaran'))


@keuangan_bp.route('/rekonsiliasi/<int:invoice_id>', methods=['POST'])
@roles_required('keuangan')
def rekonsiliasi(invoice_id: int):
    ref_no = (request.form.get('ref_no') or '').strip() or 'REF-MANUAL-BANK'
    notes = (request.form.get('notes') or '').strip() or 'Rekonsiliasi Manual'
    success, message = reconcile_manual_payment(invoice_id, ref_no, notes)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('keuangan.pembayaran'))


@keuangan_bp.route('/check_expired', methods=['POST'])
@roles_required('keuangan')
def check_expired():
    _, message = process_expired_invoices()
    flash(message, 'info')
    return redirect(url_for('keuangan.pembayaran'))


@keuangan_bp.route('/expire/<int:invoice_id>', methods=['POST'])
@roles_required('keuangan')
def mark_expired(invoice_id: int):
    success, message = expire_invoice(invoice_id)
    flash(message, 'warning' if success else 'danger')
    return redirect(url_for('keuangan.pembayaran'))
