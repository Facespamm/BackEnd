from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config
from database.db import db
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS для API
    CORS(app)

    # Инициализация базы данных
    db.init_app(app)

    # Инициализация миграций
    migrate = Migrate(app, db)

    # Инициализация API
    api = Api(
        app,
        version='1.0',
        title='Judo Tournament API',
        description='REST API для системы управления турнирами по дзюдо',
        doc='/docs/'
    )

    # Регистрация namespace'ов
    from api.auth import auth_ns
    from api.tournaments import tournaments_ns
    from api.athletes import athletes_ns
    from api.clubs import clubs_ns
    from api.fights import fights_ns
    from api.brackets import brackets_ns
    from api.results import results_ns
    from api.weighing import weighing_ns

    api.add_namespace(auth_ns, '/api/auth')
    api.add_namespace(tournaments_ns, '/api/tournaments')
    api.add_namespace(athletes_ns, '/api/athletes')
    api.add_namespace(clubs_ns, '/api/clubs')
    api.add_namespace(fights_ns, '/api/fights')
    api.add_namespace(brackets_ns, '/api/brackets')
    api.add_namespace(results_ns, '/api/results')
    api.add_namespace(weighing_ns, '/api/weighing')

    # Обработчик ошибок для API
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'message': 'Ресурс не найден',
            'error': str(error)
        }, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {
            'success': False,
            'message': 'Внутренняя ошибка сервера',
            'error': str(error)
        }, 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)