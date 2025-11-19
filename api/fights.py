from flask_restx import Namespace, Resource, fields
from flask import request
from models.fight import Fight
from services.fight_manager import FightManager

fights_ns = Namespace('fights', description='Операции со схватками')

fight_model = fights_ns.model('Fight', {
    'tournament_id': fields.Integer(required=True),
    'white_athlete_id': fields.Integer(),
    'blue_athlete_id': fields.Integer(),
    'tatami': fields.Integer(),
    'scheduled_time': fields.String()
})


@fights_ns.route('/')
class FightList(Resource):
    @fights_ns.doc('list_fights')
    def get(self):
        """Получить список схваток"""
        try:
            tournament_id = request.args.get('tournament_id', type=int)
            status = request.args.get('status')
            tatami = request.args.get('tatami', type=int)

            query = Fight.query

            if tournament_id:
                query = query.filter_by(tournament_id=tournament_id)

            if status:
                query = query.filter_by(status=status)

            if tatami:
                query = query.filter_by(tatami=tatami)

            fights = query.order_by(Fight.tatami, Fight.scheduled_time).all()

            result = []
            for fight in fights:
                fight_data = {
                    'id': fight.id,
                    'tournament_id': fight.tournament_id,
                    'tatami': fight.tatami,
                    'status': fight.status,
                    'round_number': fight.round_number,
                    'fight_number': fight.fight_number,
                    'scheduled_time': fight.scheduled_time.isoformat() if fight.scheduled_time else None,
                    'timer_seconds': fight.timer_seconds,
                    'is_golden_score': fight.is_golden_score,
                    'white_athlete': None,
                    'blue_athlete': None
                }

                if fight.white_athlete:
                    fight_data['white_athlete'] = {
                        'id': fight.white_athlete.id,
                        'name': fight.white_athlete.full_name
                    }

                if fight.blue_athlete:
                    fight_data['blue_athlete'] = {
                        'id': fight.blue_athlete.id,
                        'name': fight.blue_athlete.full_name
                    }

                result.append(fight_data)

            return {
                'success': True,
                'fights': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении схваток: {str(e)}'
            }, 500


@fights_ns.route('/<int:fight_id>/start')
@fights_ns.param('fight_id', 'ID схватки')
class StartFight(Resource):
    @fights_ns.doc('start_fight')
    def post(self, fight_id):
        """Начать схватку"""
        try:
            fight = Fight.query.get(fight_id)
            if not fight:
                return {
                    'success': False,
                    'message': 'Схватка не найдена'
                }, 404

            fight_manager = FightManager(fight_id)

            if fight_manager.start_fight():
                return {
                    'success': True,
                    'message': 'Схватка начата'
                }
            else:
                return {
                    'success': False,
                    'message': 'Не удалось начать схватку'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при запуске схватки: {str(e)}'
            }, 500