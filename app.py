from flask import Flask, render_template
from config import Config
from database.db import db, init_db
from routes import register_blueprints
from flask_login import current_user
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Создаем папку для базы данных если нет
    os.makedirs('instance', exist_ok=True)

    # Инициализация базы данных
    init_db(app)

    # Регистрация blueprint'ов
    register_blueprints(app)

    # Обработчик ошибок
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error=error), 500

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)