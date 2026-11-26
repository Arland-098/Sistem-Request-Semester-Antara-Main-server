from flask import Blueprint, flash, redirect, render_template, request, url_for

from routes.decorators import roles_required
from services import get_all_invoices, reconcile_manual_payment, set_config

keuangan_bp = Blueprint('keuangan', __name__, url_prefix='/keuangan')


@keuangan_bp.route('/tarif')
@roles_required('admin_akademik')
def tarif():
    return render_template('keuangan_tarif.html', active_tab='keuangan_tarif')


@keuangan_bp.route('/tarif/update', methods=['POST'])
@roles_required('admin_akademik')
def tarif_update():
    raw_rate = request.form.get('sks_rate', '220000')
    try:
        parsed_rate = int(raw_rate)
    except (TypeError, ValueError):
        flash("Nominal tarif biaya per SKS harus berupa angka valid.", "danger")
        return redirect(url_for('keuangan.tarif'))

    if parsed_rate < 0:
        flash("Nominal tarif biaya per SKS tidak boleh bernilai negatif.", "danger")
        return redirect(url_for('keuangan.tarif'))

    set_config('sks_rate', parsed_rate)
    flash(
        f"Tarif biaya per SKS berhasil diperbarui menjadi Rp{parsed_rate:,} sesuai SK Rektor No. 686 Tahun 2025.",
        "success",
    )
    return redirect(url_for('keuangan.tarif'))


@keuangan_bp.route('/pembayaran')
@roles_required('admin_akademik')
def pembayaran():
    invoices = get_all_invoices()
    return render_template('keuangan_pembayaran.html', invoices=invoices, active_tab='keuangan_pembayaran')


@keuangan_bp.route('/rekonsiliasi/<int:invoice_id>', methods=['POST'])
@roles_required('admin_akademik')
def rekonsiliasi(invoice_id: int):
    ref_no = (request.form.get('ref_no') or '').strip() or 'REF-MANUAL-BANK'
    notes = (request.form.get('notes') or '').strip() or 'Rekonsiliasi Manual'
    reconcile_manual_payment(invoice_id, ref_no, notes)
    flash(f"Pembayaran Virtual Account faktur #{invoice_id} berhasil DIREKONSILIASI LUNAS.", "success")
    return redirect(url_for('keuangan.pembayaran'))
