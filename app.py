import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from blueprints import register_blueprints
from database.db import init_db
from flasgger import Swagger
from init_database.init_db import init_dans_new, init_roles_new, init_category, init_admin

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DOCKER_CONNECTION')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'cc820b15d44f7643fa52046a6c34f98a804c35d5ebdf830204a074c2c0059f88')

CORS(app)
jwt = JWTManager(app)

# ── Инициализация БД ──────────────────────────────────────────────
init_db(app)
# ── Blueprints ────────────────────────────────────────────────────
register_blueprints(app)
with app.app_context():
    init_dans_new()
    init_roles_new()
    init_category()
    init_admin()

# ── Swagger ───────────────────────────────────────────────────────
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)