from flask import Flask

def register_blueprints(app: Flask):
    """Решистрациия blueprint"""
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
    from api.user import user_bp
    from api.pdf_routes import pdf_bp
    from api.scores import scores_bp

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
    app.register_blueprint(user_bp)