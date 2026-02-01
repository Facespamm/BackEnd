from flask import request, Blueprint, jsonify

from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.tournament_repo import TournamentRepository
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint('brackets', __name__, url_prefix='/api/brackets')

@brackets_bp.route('/<int:tournament_id>', methods=['POST'])
def create_bracket(tournament_id):
    """Создать новую сетку"""
    try:
        if  not tournament_id:
            return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        tournament_repo = TournamentRepository()
        tournament = tournament_repo.get_tournament_by_id(tournament_id)
        categories = tournament_repo.get_category(tournament_id)
        if not tournament or not categories:
            return jsonify({'success': False, 'message': 'Турнир или категория не найдены'}), 404

        bracket_generator = BracketGenerator(tournament_id)
        generate_fights = bracket_generator.generate_olympic(category_id)

        if not generate_fights:
            return jsonify({
                'success': False,
                'message': 'Сетка не создала бои'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Сетка успешно создана'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания сетки: {str(e)}'}), 500

@brackets_bp.route('/<int:tournament_id>/fights/', methods=['GET'])
def fight_bracket(tournament_id):
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': f'ID турнира не указан'})

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        tournament_repo = TournamentRepository()
        tournament_category_id = tournament_repo.get_tournament_category_id(tournament_id, category_id)

        fight_repo = FightRepository()
        fights = fight_repo.get_fight_by_tournament(tournament_category_id)

        fights_dtos = []

        athlete_repo = AthleteRepository()
        for fight in fights:
            fights_dtos.append({
                'id': fight.id,
                'blue_athlete': athlete_repo.get_athlete_by_fight(fight.blue_athlete_id, fight.id),
                'white_athlete': athlete_repo.get_athlete_by_fight(fight.white_athlete_id, fight.id),
                'tatami_number': fight.tatami_number,
                'round': fight.round_number,
                'status_fight': fight.status.value
            })

        tournament_repo = TournamentRepository()
        tournament_name = tournament_repo.get_tournament_name_by_tournament_category(tournament_category_id)

        if not fights_dtos:
            return jsonify({
                'success': False,
                'message': 'Нет боев'
            }), 404

        return jsonify({
            'success': True,
            'fights': fights_dtos,
            'tournament_name': tournament_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка вывода боев: {str(e)}'
        }), 500