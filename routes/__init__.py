"""
Регистрация всех blueprint'ов приложения
"""

from .main import main_bp
from .admin import admin_bp
from .athletes import athletes_bp
from .tournaments import tournaments_bp
from .weighing import weighing_bp
from .brackets import brackets_bp
from .fights import fights_bp
from .referee import referee_bp
from .scoreboard import scoreboard_bp
from .public import public_bp
from .api import api_bp

def register_blueprints(app):
    """Регистрация всех blueprint'ов"""
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(athletes_bp, url_prefix='/admin/athletes')
    app.register_blueprint(tournaments_bp, url_prefix='/admin/tournaments')
    app.register_blueprint(weighing_bp, url_prefix='/admin/weighing')
    app.register_blueprint(brackets_bp, url_prefix='/admin/brackets')
    app.register_blueprint(fights_bp, url_prefix='/admin/fights')
    app.register_blueprint(referee_bp, url_prefix='/referee')
    app.register_blueprint(scoreboard_bp, url_prefix='/scoreboard')
    app.register_blueprint(public_bp, url_prefix='/public')
    app.register_blueprint(api_bp, url_prefix='/api')