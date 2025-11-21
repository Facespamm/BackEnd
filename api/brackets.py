from flask import request, Blueprint, jsonify
from models.bracket import Bracket
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint('brackets', __name__, url_prefix='/api/brackets')  # не забудь /api, если нужно


@brackets_bp.route('/', methods=['GET'])
def get_brackets_list():  # ← переименовал
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

        return jsonify({
            'success': True,
            'brackets': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении сеток: {str(e)}'
        }), 500


@brackets_bp.route('/<int:bracket_id>/generate', methods=['POST'])
def generate_bracket(bracket_id):  # ← тоже лучше переименовать, чтобы не было конфликтов
    """Сгенерировать схватки для сетки"""
    try:
        bracket = Bracket.query.get(bracket_id)
        if not bracket:
            return jsonify({'success': False, 'message': 'Сетка не найдена'}), 404

        if bracket.athletes_count < 2:
            return jsonify({'success': False, 'message': 'Для генерации сетки нужно минимум 2 участника'}), 400

        generator = BracketGenerator(bracket)
        fights = generator.generate()

        if fights:
            return jsonify({
                'success': True,
                'message': f'Сетка успешно сгенерирована. Создано {len(fights)} схваток.',
                'fights_count': len(fights)
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Ошибка при генерации сетки'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при генерации сетки: {str(e)}'}), 500


@brackets_bp.route('/<int:bracket_id>/fights', methods=['GET'])
def get_bracket_fights(bracket_id):  # ← переименовал — теперь всё ок!
    """Получить схватки сетки"""
    try:
        bracket = Bracket.query.get(bracket_id)
        if not bracket:
            return jsonify({'success': False, 'message': 'Сетка не найдена'}), 404

        fights_by_round = {}
        for fight in bracket.fights:
            round_num = fight.round_number
            if round_num not in fights_by_round:
                fights_by_round[round_num] = []

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

            if fight.result and fight.result.winner:
                fight_data['winner'] = {
                    'id': fight.result.winner_id,
                    'name': fight.result.winner.full_name
                }

            fights_by_round[round_num].append(fight_data)

        return jsonify({
            'success': True,
            'bracket': bracket.name,
            'fights_by_round': fights_by_round
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схваток сетки: {str(e)}'
        }), 500