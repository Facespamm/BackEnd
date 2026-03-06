import hashlib
import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from api.pdf_routes import pdf_bp
from api.scores import scores_bp
from database.db import init_db, db
from flasgger import Swagger
from init_database.init_db import init_dans_new, init_roles_new, init_category

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DOCKER_CONNECTION')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'cc820b15d44f7643fa52046a6c34f98a804c35d5ebdf830204a074c2c0059f88')

CORS(app)
jwt = JWTManager(app)

# ── Инициализация БД ──────────────────────────────────────────────
init_db(app)

def hash_password(password):
    salt = 'judo_tournament_salt_2024'
    return hashlib.sha256((password + salt).encode()).hexdigest()

with app.app_context():
    init_dans_new()
    init_roles_new()
    init_category()

    from new_model.head_model.new_user import UserNew
    from new_model.handbook.role_new import RoleNew

    try:
        admin = UserNew.query.filter_by(username='admin').first()
        if not admin:
            role = RoleNew.query.filter_by(name='Администратор').first()
            if role:
                admin = UserNew(
                    username='admin',
                    password_hash=hash_password('admin123'),
                    first_name='Главный',
                    middle_name='',
                    last_name='Администратор',
                    email='admin@judo.kz',
                    phone='',
                    roles=[role]
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Админ создан: login=admin, password=admin123")
            else:
                print("⚠️ Роль 'Администратор' не найдена")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка создания админа: {e}")

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

# ── Blueprints ────────────────────────────────────────────────────
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
from api.dan import dans_bp
from api.referee import referee_bp

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
app.register_blueprint(dans_bp)
app.register_blueprint(referee_bp)
app.register_blueprint(scores_bp)
app.register_blueprint(pdf_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)