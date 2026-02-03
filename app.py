import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api
from database.db import init_db
from flasgger import Swagger

from init_database.init_db import init_dans_new, init_roles_new

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DOCKER_CONNECTION')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
# CORS для API
CORS(app)
jwt = JWTManager(app)

# Инициализация базы данных
init_db(app)

with app.app_context():
    init_dans_new()
    init_roles_new()

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Clubs API",
        "description": "API для управления спортивными клубами",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# # Регистрация namespace'ов
from api.auth import auth_bp
from api.tournaments import tournaments_bp
from api.athletes import athletes_bp
from api.clubs import clubs_bp
from api.statistics import statistics_bp
from api.fights import fights_bp
from api.brackets import brackets_bp
from api.results import results_bp
from api.weighing import weighing_bp
from api.categories import categories_bp
# from api.registrations import registrations_bp
from api.dan import dans_bp
from api.referee import referee_bp
# from api.scores import scores_bp

app.register_blueprint(auth_bp)
app.register_blueprint(tournaments_bp)
app.register_blueprint(athletes_bp)

app.register_blueprint(statistics_bp)
app.register_blueprint(clubs_bp)
app.register_blueprint(fights_bp)
app.register_blueprint(brackets_bp)
app.register_blueprint(results_bp)
app.register_blueprint(weighing_bp)
app.register_blueprint(categories_bp)
# app.register_blueprint(registrations_bp)
app.register_blueprint(dans_bp)
app.register_blueprint(referee_bp)
# app.register_blueprint(scores_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
