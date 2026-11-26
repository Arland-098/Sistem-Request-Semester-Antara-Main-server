from flask import Flask

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.dosen import dosen_bp
from routes.dpa import dpa_bp
from routes.keuangan import keuangan_bp
from routes.mahasiswa import mahasiswa_bp
from routes.main import main_bp
from routes.master import master_bp
from routes.prodi import prodi_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(mahasiswa_bp)
    app.register_blueprint(dpa_bp)
    app.register_blueprint(dosen_bp)
    app.register_blueprint(prodi_bp)
    app.register_blueprint(keuangan_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(admin_bp)
