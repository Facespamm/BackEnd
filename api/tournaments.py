from flask_restx import Namespace, Resource, fields
from flask import request
from models.tournament import Tournament
from models.category import Category
from database.db import db

tournaments_ns = Namespace('tournaments', description='Операции с турнирами')

category_model = tournaments_ns.model('Category', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'gender': fields.String(required=True),
    'min_weight': fields.Float(),
    'max_weight': fields.Float(),
    'min_age': fields.Integer(),
    'max_age': fields.Integer(),
    'athletes_count': fields.Integer(readonly=True)
})

tournament_model = tournaments_ns.model('Tournament', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'description': fields.String(),
    'start_date': fields.String(required=True),
    'end_date': fields.String(required=True),
    'venue': fields.String(),
    'city': fields.String(),
    'country': fields.String(),
    'status': fields.String(),
    'tatami_count': fields.Integer(),
    'athletes_count': fields.Integer(readonly=True),
    'progress_percentage': fields.Integer(readonly=True)
})


@tournaments_ns.route('/')
class TournamentList(Resource):
    @tournaments_ns.marshal_list_with(tournament_model)
    def get(self):
        """Получить список всех турниров"""
        status = request.args.get('status')

        query = Tournament.query
        if status:
            query = query.filter_by(status=status)

        return query.order_by(Tournament.start_date.desc()).all()

    @tournaments_ns.expect(tournament_model)
    @tournaments_ns.marshal_with(tournament_model)
    def post(self):
        """Создать новый турнир"""
        data = request.json

        tournament = Tournament(
            name=data['name'],
            description=data.get('description'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            venue=data.get('venue'),
            city=data.get('city'),
            country=data.get('country', 'Россия'),
            tatami_count=data.get('tatami_count', 1)
        )

        if tournament.save():
            return tournament, 201
        else:
            tournaments_ns.abort(400, 'Ошибка при создании турнира')


@tournaments_ns.route('/<int:tournament_id>')
class TournamentDetail(Resource):
    @tournaments_ns.marshal_with(tournament_model)
    def get(self, tournament_id):
        """Получить информацию о турнире"""
        tournament = Tournament.query.get_or_404(tournament_id)
        return tournament

    @tournaments_ns.expect(tournament_model)
    @tournaments_ns.marshal_with(tournament_model)
    def put(self, tournament_id):
        """Обновить информацию о турнире"""
        tournament = Tournament.query.get_or_404(tournament_id)
        data = request.json

        for key, value in data.items():
            if hasattr(tournament, key):
                setattr(tournament, key, value)

        if tournament.save():
            return tournament
        else:
            tournaments_ns.abort(400, 'Ошибка при обновлении турнира')

    def delete(self, tournament_id):
        """Удалить турнир"""
        tournament = Tournament.query.get_or_404(tournament_id)

        if tournament.delete():
            return {'success': True, 'message': 'Турнир удален'}
        else:
            tournaments_ns.abort(400, 'Ошибка при удалении турнира')


@tournaments_ns.route('/<int:tournament_id>/categories')
class TournamentCategories(Resource):
    @tournaments_ns.marshal_list_with(category_model)
    def get(self, tournament_id):
        """Получить категории турнира"""
        tournament = Tournament.query.get_or_404(tournament_id)
        return tournament.categories