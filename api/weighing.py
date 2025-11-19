from flask_restx import Namespace, Resource, fields
from flask import request
from models.weighing import Weighing
from models.tournament import Tournament
from models.athlete import Athlete

weighing_ns = Namespace('weighing', description='Операции со взвешиванием')

weighing_model = weighing_ns.model('Weighing', {
    'tournament_id': fields.Integer(required=True),
    'athlete_id': fields.Integer(required=True),
    'weight': fields.Float(required=True),
    'notes': fields.String()
})


@weighing_ns.route('/')
class WeighingList(Resource):
    @weighing_ns.doc('list_weighings')
    def get(self):
        """Получить список взвешиваний"""
        try:
            tournament_id = request.args.get('tournament_id', type=int)
            athlete_id = request.args.get('athlete_id', type=int)

            query = Weighing.query

            if tournament_id:
                query = query.filter_by(tournament_id=tournament_id)

            if athlete_id:
                query = query.filter_by(athlete_id=athlete_id)

            weighings = query.order_by(Weighing.weighing_time.desc()).all()

            result = []
            for weighing in weighings:
                result.append({
                    'id': weighing.id,
                    'athlete_name': weighing.athlete.full_name if weighing.athlete else None,
                    'weight': weighing.weight,
                    'weight_category': weighing.weight_category,
                    'tournament_name': weighing.tournament.name if weighing.tournament else None,
                    'weighing_time': weighing.weighing_time.isoformat(),
                    'status': weighing.status_display,
                    'is_valid': weighing.is_valid
                })

            return {
                'success': True,
                'weighings': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении взвешиваний: {str(e)}'
            }, 500

    @weighing_ns.expect(weighing_model)
    @weighing_ns.doc('create_weighing')
    def post(self):
        """Создать запись о взвешивании"""
        try:
            data = request.json

            if not data.get('tournament_id') or not data.get('athlete_id') or not data.get('weight'):
                return {
                    'success': False,
                    'message': 'Обязательные поля: tournament_id, athlete_id, weight'
                }, 400

            # Проверяем существование турнира и участника
            tournament = Tournament.query.get(data['tournament_id'])
            athlete = Athlete.query.get(data['athlete_id'])

            if not tournament:
                return {
                    'success': False,
                    'message': 'Турнир не найден'
                }, 404

            if not athlete:
                return {
                    'success': False,
                    'message': 'Участник не найден'
                }, 404

            weighing = Weighing(
                tournament_id=data['tournament_id'],
                athlete_id=data['athlete_id'],
                weight=data['weight'],
                notes=data.get('notes')
            )

            # Определяем категорию
            weighing.determine_category()

            if weighing.save():
                return {
                    'success': True,
                    'message': 'Взвешивание успешно записано',
                    'weighing_id': weighing.id,
                    'weight_category': weighing.weight_category,
                    'status': weighing.status_display
                }, 201
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при сохранении взвешивания'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании записи взвешивания: {str(e)}'
            }, 500