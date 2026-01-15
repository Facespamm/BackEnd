from flask import request, Blueprint, jsonify
from models.bracket import Bracket
from new_model.head_model.tournament_new import TournamentNew
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint('brackets', __name__, url_prefix='/api/brackets')

@brackets_bp.route('/<int:tournament_id>', methods=['POST'])
def create_bracket(tournament_id):
    """Создать новую сетку"""
    try:
        if  not tournament_id:
            return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

        tournament = TournamentNew.query.get(tournament_id)

        if not tournament or not tournament.categories:
            return jsonify({'success': False, 'message': 'Турнир или категория не найдены'}), 404

        bracket_generator = BracketGenerator()
        bracket_generator.generate()

        return jsonify({
            'success': True,
            'message': 'Сетка успешно создана',
            'bracket_id': bracket.id
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания сетки: {str(e)}'}), 500

@brackets_bp.route('/<int:bracket_id>/fights', methods=['GET'])
def get_bracket_fights(bracket_id):
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