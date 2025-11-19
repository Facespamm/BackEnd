from flask_restx import Namespace, Resource, fields
from flask import request
from models.bracket import Bracket
from models.category import Category
from services.bracket_generator import BracketGenerator

brackets_ns = Namespace('brackets', description='Операции с турнирными сетками')

bracket_model = brackets_ns.model('Bracket', {
    'tournament_id': fields.Integer(required=True),
    'category_id': fields.Integer(required=True),
    'name': fields.String(required=True),
    'bracket_type': fields.String(required=True)
})


@brackets_ns.route('/')
class BracketList(Resource):
    @brackets_ns.doc('list_brackets')
    def get(self):
        """Получить список сеток"""
        try:
            tournament_id = request.args.get('tournament_id', type=int)
            category_id = request.args.get('category_id', type=int)

            query = Bracket.query

            if tournament_id:
                query = query.filter_by(tournament_id=tournament_id)

            if category_id:
                query = query.filter_by(category_id=category_id)

            brackets = query.all()

            result = []
            for bracket in brackets:
                result.append({
                    'id': bracket.id,
                    'name': bracket.name,
                    'bracket_type': bracket.bracket_type,
                    'status': bracket.status,
                    'tournament_id': bracket.tournament_id,
                    'category_id': bracket.category_id,
                    'progress_percentage': bracket.progress_percentage,
                    'athletes_count': bracket.athletes_count
                })

            return {
                'success': True,
                'brackets': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении сеток: {str(e)}'
            }, 500


@brackets_ns.route('/<int:bracket_id>/generate')
@brackets_ns.param('bracket_id', 'ID сетки')
class GenerateBracket(Resource):
    @brackets_ns.doc('generate_bracket')
    def post(self, bracket_id):
        """Сгенерировать схватки для сетки"""
        try:
            bracket = Bracket.query.get(bracket_id)
            if not bracket:
                return {
                    'success': False,
                    'message': 'Сетка не найдена'
                }, 404

            if bracket.athletes_count < 2:
                return {
                    'success': False,
                    'message': 'Для генерации сетки нужно минимум 2 участника'
                }, 400

            generator = BracketGenerator(bracket)
            fights = generator.generate()

            if fights:
                return {
                    'success': True,
                    'message': f'Сетка успешно сгенерирована. Создано {len(fights)} схваток.',
                    'fights_count': len(fights)
                }
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при генерации сетки'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при генерации сетки: {str(e)}'
            }, 500


@brackets_ns.route('/<int:bracket_id>/fights')
@brackets_ns.param('bracket_id', 'ID сетки')
class BracketFights(Resource):
    @brackets_ns.doc('get_bracket_fights')
    def get(self, bracket_id):
        """Получить схватки сетки"""
        try:
            bracket = Bracket.query.get(bracket_id)
            if not bracket:
                return {
                    'success': False,
                    'message': 'Сетка не найдена'
                }, 404

            fights_by_round = {}
            for fight in bracket.fights:
                if fight.round_number not in fights_by_round:
                    fights_by_round[fight.round_number] = []

                fight_data = {
                    'id': fight.id,
                    'fight_number': fight.fight_number,
                    'status': fight.status,
                    'white_athlete': None,
                    'blue_athlete': None,
                    'winner': None
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

                if fight.result:
                    fight_data['winner'] = {
                        'id': fight.result.winner_id,
                        'name': fight.result.winner.full_name
                    }

                fights_by_round[fight.round_number].append(fight_data)

            return {
                'success': True,
                'bracket': bracket.name,
                'fights_by_round': fights_by_round
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении схваток сетки: {str(e)}'
            }, 500