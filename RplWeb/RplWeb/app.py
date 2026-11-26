import os
import csv
import io
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, Response
)
import database

app = Flask(
    __name__,
    static_folder='Portal Akademik_files',
    static_url_path='/Portal Akademik_files'
)
app.secret_key = 'uin-semesta-semester-antara-secret-key-2026'

# Ensure database is initialized
database.init_db()

@app.context_processor
def inject_global_vars():
    user_id = session.get('user_id', 1) # Default: Ihsan Mubarok (Mahasiswa)
    user = database.get_user_by_id(user_id)
    if not user:
        user = database.get_user_by_id(1)
    
    return {
        'current_user': user,
        'active_semester': database.get_config('active_semester', 'Semester Antara 2026/2027'),
        'reg_status': database.get_config('registration_status', 'Buka'),
        'reg_start': database.get_config('registration_start', '2026-07-01'),
        'reg_end': database.get_config('registration_end', '2026-07-25'),
        'sks_rate': int(database.get_config('sks_rate', '220000')),
        'max_sks': int(database.get_config('max_sks', '9'))
    }

# Quick switch role for testing and review
@app.route('/switch_role/<role_name>')
def switch_role(role_name):
    role_map = {
        'mahasiswa': 1, # Ihsan Mubarok
        'dpa': 5,       # Dr. Dewi Khairani, M.Sc.
        'dosen': 6,     # Luh Kesuma Wardhani, S.T., M.T.
        'prodi': 7,     # Admin Prodi TI
        'keuangan': 8   # Biro Keuangan
    }
    target_id = role_map.get(role_name, 1)
    session['user_id'] = target_id
    user = database.get_user_by_id(target_id)
    flash(f"Berhasil beralih peran ke: {user['name']} ({user['role'].upper()})", "info")
    
    # Redirect to corresponding role home
    if role_name == 'mahasiswa':
        return redirect(url_for('mahasiswa_krs'))
    elif role_name == 'dpa':
        return redirect(url_for('dpa_dashboard'))
    elif role_name == 'dosen':
        return redirect(url_for('dosen_dashboard'))
    elif role_name == 'prodi':
        return redirect(url_for('prodi_monitoring'))
    elif role_name == 'keuangan':
        return redirect(url_for('keuangan_pembayaran'))
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html', active_tab='home')

# ==========================================
# 1) MAHASISWA ROUTES (FR-03, FR-04, FR-07)
# ==========================================

# FR-03: Katalog Resmi Mata Kuliah yang Dibuka
@app.route('/katalog')
def mahasiswa_katalog():
    courses = database.get_courses_list()
    grouped_courses = database.get_courses_grouped_by_semester()
    selected_prodi = request.args.get('prodi', '60')
    return render_template(
        'mahasiswa_katalog.html', 
        courses=courses, 
        grouped_courses=grouped_courses,
        selected_prodi=selected_prodi,
        active_tab='katalog'
    )

# FR-04: Pengisian KRS dengan Validasi Akademik & NFR-03 Keandalan Kuota
@app.route('/krs')
def mahasiswa_krs():
    user_id = session.get('user_id', 1)
    student = database.get_user_by_id(user_id)
    app_data, krs_items, invoice = database.get_student_application(user_id)
    courses = database.get_courses_list()
    grouped_courses = database.get_courses_grouped_by_semester()
    
    current_selected_ids = [item['course_id'] for item in krs_items] if krs_items else []
    
    return render_template(
        'mahasiswa_krs.html',
        student=student,
        app=app_data,
        krs_items=krs_items,
        invoice=invoice,
        available_courses=courses,
        grouped_courses=grouped_courses,
        current_selected_ids=current_selected_ids,
        active_tab='krs'
    )

@app.route('/krs/submit', methods=['POST'])
def krs_submit():
    user_id = session.get('user_id', 1)
    course_ids = request.form.getlist('course_ids', type=int)

    success, message = database.submit_student_krs(user_id, course_ids)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('mahasiswa_krs'))

# FR-07: Rincian Tagihan Virtual Account & Pemantauan Status Pembayaran
@app.route('/tagihan')
def mahasiswa_tagihan():
    user_id = session.get('user_id', 1)
    student = database.get_user_by_id(user_id)
    app_data, krs_items, invoice = database.get_student_application(user_id)

    return render_template(
        'mahasiswa_tagihan.html',
        student=student,
        app=app_data,
        invoice=invoice,
        items=krs_items,
        active_tab='tagihan'
    )

# FR-07: Cetak Kartu Rencana Studi Sah
@app.route('/cetak_krs')
def cetak_krs():
    user_id = session.get('user_id', 1)
    student = database.get_user_by_id(user_id)
    app_data, krs_items, invoice = database.get_student_application(user_id)

    if not app_data or app_data['status'] != 'Lunas':
        flash("Pencetakan Kartu Rencana Studi Sah hanya dapat dilakukan setelah status pembayaran lunas.", "warning")
        return redirect(url_for('mahasiswa_tagihan'))

    return render_template(
        'mahasiswa_cetak_krs.html',
        student=student,
        app=app_data,
        items=krs_items,
        invoice=invoice
    )

# ==========================================
# 2) DOSEN PEMBIMBING AKADEMIK (FR-08, FR-09)
# ==========================================

# FR-08: Dasbor Pengajuan Rencana Studi Bimbingan
@app.route('/dpa')
def dpa_dashboard():
    user_id = session.get('user_id', 5) # Default: Dr. Dewi Khairani
    applications = database.get_dpa_applications(user_id)
    return render_template('dpa_dashboard.html', applications=applications, active_tab='dpa')

# FR-09: Verifikasi Persetujuan DPA
@app.route('/dpa/approve/<int:app_id>', methods=['POST'])
def dpa_approve(app_id):
    database.approve_student_krs(app_id)
    flash(f"Pengajuan KRS #{app_id} berhasil DISETUJUI. Tagihan Virtual Account resmi telah diterbitkan secara otomatis.", "success")
    return redirect(url_for('dpa_dashboard'))

# FR-09: Verifikasi Penolakan DPA
@app.route('/dpa/reject/<int:app_id>', methods=['POST'])
def dpa_reject(app_id):
    notes = request.form.get('notes', 'Pengajuan ditolak oleh DPA.')
    database.reject_student_krs(app_id, notes)
    flash(f"Pengajuan KRS #{app_id} telah DITOLAK dengan catatan: '{notes}'. Mahasiswa dapat melakukan perbaikan.", "warning")
    return redirect(url_for('dpa_dashboard'))

# ==========================================
# 3) DOSEN PENGAMPU (FR-10, FR-11)
# ==========================================

# FR-10 & FR-11: Konfirmasi Kesediaan Mengajar & Kelas Dispensasi
@app.route('/dosen')
def dosen_dashboard():
    user_id = session.get('user_id', 6) # Default: Luh Kesuma Wardhani
    courses = database.get_courses_list()
    # Filter courses assigned to this lecturer
    my_courses = [c for c in courses if c['lecturer_id'] == user_id]
    return render_template('dosen_dashboard.html', courses=my_courses, active_tab='dosen')

@app.route('/dosen/confirm/<int:course_id>', methods=['POST'])
def dosen_confirm(course_id):
    agreed = request.form.get('agreed') == '1'
    database.confirm_lecturer_teaching(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR" if agreed else "MENOLAK MENGAJAR"
    flash(f"Konfirmasi mengajar berhasil disimpan: {status_str}.", "success")
    return redirect(url_for('dosen_dashboard'))

@app.route('/dosen/dispensasi/<int:course_id>', methods=['POST'])
def dosen_dispensasi(course_id):
    agreed = request.form.get('agreed') == '1'
    database.confirm_lecturer_dispensation(course_id, agreed)
    status_str = "BERSEDIA MENGAJAR KELAS DISPENSASI" if agreed else "MENOLAK KELAS DISPENSASI"
    flash(f"Konfirmasi kelas dispensasi berhasil disimpan: {status_str}.", "info")
    return redirect(url_for('dosen_dashboard'))

# ==========================================
# 4) PROGRAM STUDI
# ==========================================

# Pengaturan Periode & Status Keaktifan Semester Antara
@app.route('/prodi/periode')
def prodi_periode():
    return render_template('prodi_periode.html', active_tab='prodi_periode')

@app.route('/prodi/periode/update', methods=['POST'])
def prodi_periode_update():
    database.set_config('active_semester', request.form.get('active_semester'))
    database.set_config('registration_status', request.form.get('registration_status'))
    database.set_config('registration_start', request.form.get('registration_start'))
    database.set_config('registration_end', request.form.get('registration_end'))
    database.set_config('max_sks', request.form.get('max_sks', '9'))
    flash("Pengaturan periode pendaftaran Semester Antara berhasil diperbarui.", "success")
    return redirect(url_for('prodi_periode'))

# Pengelolaan Katalog MK yang Dibuka
@app.route('/prodi/katalog')
def prodi_katalog():
    courses = database.get_courses_list()
    lecturers = database.get_users_by_role('dosen') + database.get_users_by_role('dpa')
    return render_template('prodi_katalog.html', courses=courses, lecturers=lecturers, active_tab='prodi_katalog')

@app.route('/prodi/katalog/add', methods=['POST'])
def prodi_katalog_add():
    code = request.form.get('code')
    name = request.form.get('name')
    sks = int(request.form.get('sks', 3))
    quota = int(request.form.get('quota', 30))
    lecturer_id = int(request.form.get('lecturer_id'))
    schedule_day = request.form.get('schedule_day', 'Senin')
    schedule_time = request.form.get('schedule_time', '08.00 - 10.30 WIB')
    room = request.form.get('room', 'Ruang Kelas FST')

    database.add_course(code, name, sks, schedule_day, schedule_time, room, quota, lecturer_id)
    flash(f"Mata kuliah {code} - {name} berhasil ditambahkan ke katalog resmi.", "success")
    return redirect(url_for('prodi_katalog'))

@app.route('/prodi/katalog/edit/<int:course_id>', methods=['POST'])
def prodi_katalog_edit(course_id):
    name = request.form.get('name')
    sks = int(request.form.get('sks', 3))
    quota = int(request.form.get('quota', 30))
    lecturer_id = int(request.form.get('lecturer_id'))
    schedule_day = request.form.get('schedule_day')
    schedule_time = request.form.get('schedule_time')
    room = request.form.get('room')

    database.update_course_details(course_id, name, sks, schedule_day, schedule_time, room, quota, lecturer_id)
    flash(f"Data mata kuliah #{course_id} berhasil diperbarui.", "success")
    return redirect(url_for('prodi_katalog'))

@app.route('/prodi/katalog/delete/<int:course_id>', methods=['POST'])
def prodi_katalog_delete(course_id):
    database.delete_course(course_id)
    flash(f"Mata kuliah #{course_id} telah dihapus dari katalog.", "warning")
    return redirect(url_for('prodi_katalog'))

# Pengelolaan Jadwal Kuliah Luring & Alokasi Ruang Kelas
@app.route('/prodi/jadwal_ruang')
def prodi_jadwal_ruang():
    courses = database.get_courses_list()
    return render_template('prodi_jadwal_ruang.html', courses=courses, active_tab='prodi_jadwal')

@app.route('/prodi/jadwal/update/<int:course_id>', methods=['POST'])
def prodi_jadwal_update(course_id):
    day = request.form.get('schedule_day')
    time_str = request.form.get('schedule_time')
    room = request.form.get('room')

    conn = database.get_db()
    cur = conn.cursor()
    cur.execute('''
    UPDATE courses 
    SET schedule_day = ?, schedule_time = ?, room = ? 
    WHERE id = ?
    ''', (day, time_str, room, course_id))
    conn.commit()
    conn.close()

    flash(f"Jadwal dan alokasi ruang kuliah luring berhasil diperbarui.", "success")
    return redirect(url_for('prodi_jadwal_ruang'))

# Pemantauan Kuota Pendaftar & Penetapan Status Kelas
@app.route('/prodi/monitoring')
def prodi_monitoring():
    courses = database.get_courses_list()
    return render_template('prodi_monitoring.html', courses=courses, active_tab='prodi_monitoring')

@app.route('/prodi/status/<int:course_id>', methods=['POST'])
def prodi_set_class_status(course_id):
    new_status = request.form.get('status')
    database.update_course_status(course_id, new_status)
    flash(f"Status kelas #{course_id} berhasil ditetapkan menjadi: {new_status}.", "success")
    return redirect(url_for('prodi_monitoring'))

# Penutupan Pendaftaran & Ekspor Peserta Resmi
@app.route('/prodi/rekap')
def prodi_rekap():
    participants = database.get_official_participants()
    return render_template('prodi_rekap.html', participants=participants, active_tab='prodi_rekap')

@app.route('/prodi/tutup', methods=['POST'])
def prodi_tutup():
    database.set_config('registration_status', 'Tutup')
    flash("Pendaftaran Semester Antara resmi DITUTUP. Akses pengisian KRS bagi mahasiswa telah dikunci.", "warning")
    return redirect(url_for('prodi_rekap'))

@app.route('/prodi/buka', methods=['POST'])
def prodi_buka():
    database.set_config('registration_status', 'Buka')
    flash("Pendaftaran Semester Antara telah DIBUKA kembali.", "success")
    return redirect(url_for('prodi_rekap'))

@app.route('/prodi/export_csv')
def prodi_export_csv():
    participants = database.get_official_participants()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'NO', 'NIM', 'NAMA MAHASISWA', 'PROGRAM STUDI',
        'KODE MK', 'NAMA MATA KULIAH', 'SKS', 'RUANG KELAS',
        'HARI', 'WAKTU', 'DOSEN PENGAMPU', 'STATUS PEMBAYARAN', 'NO VIRTUAL ACCOUNT'
    ])

    for i, p in enumerate(participants, 1):
        writer.writerow([
            i, p['nim_nip'], p['student_name'], p['prodi'],
            p['course_code'], p['course_name'], p['sks'], p['room'],
            p['schedule_day'], p['schedule_time'], p['lecturer_name'],
            p['payment_status'], p['va_number'] or '-'
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={"Content-Disposition": "attachment;filename=Rekapitulasi_Peserta_Semester_Antara_2026.csv"}
    )

# ==========================================
# 5) BAGIAN KEUANGAN
# ==========================================

# Pengaturan Tarif Biaya per SKS (SK Rektor 686/2025)
@app.route('/keuangan/tarif')
def keuangan_tarif():
    return render_template('keuangan_tarif.html', active_tab='keuangan_tarif')

@app.route('/keuangan/tarif/update', methods=['POST'])
def keuangan_tarif_update():
    new_rate = request.form.get('sks_rate', '220000')
    database.set_config('sks_rate', new_rate)
    flash(f"Tarif biaya per SKS berhasil diperbarui menjadi Rp{int(new_rate):,} sesuai SK Rektor No. 686 Tahun 2025.", "success")
    return redirect(url_for('keuangan_tarif'))

# Pemantauan VA & Rekonsiliasi Manual
@app.route('/keuangan/pembayaran')
def keuangan_pembayaran():
    invoices = database.get_all_invoices()
    return render_template('keuangan_pembayaran.html', invoices=invoices, active_tab='keuangan_pembayaran')

@app.route('/keuangan/rekonsiliasi/<int:invoice_id>', methods=['POST'])
def keuangan_rekonsiliasi(invoice_id):
    ref_no = request.form.get('ref_no', 'REF-MANUAL-BANK')
    notes = request.form.get('notes', 'Rekonsiliasi Manual')
    database.reconcile_manual_payment(invoice_id, ref_no, notes)
    flash(f"Pembayaran Virtual Account faktur #{invoice_id} berhasil DIREKONSILIASI LUNAS.", "success")
    return redirect(url_for('keuangan_pembayaran'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
