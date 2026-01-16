from flask import request, Blueprint, jsonify
from models.bracket import Bracket
from new_model.head_model.tournament_new import TournamentNew
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

        tournament_repo = TournamentRepository()
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

        if not tournament or not tournament.categories:
            return jsonify({'success': False, 'message': 'Турнир или категория не найдены'}), 404

        bracket_generator = BracketGenerator(tournament_id)
        bracket_generator.generate()

        return jsonify({
            'success': True,
            'message': 'Сетка успешно создана',
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания сетки: {str(e)}'}), 500

@brackets_bp.route('/<int:tournament_id>/fights/', methods=['GET'])
def fight_bracket(tournament_id):
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': f'ID турнира не указан'})

        fight_repo = FightRepository()
        fights = fight_repo.get_fight_by_tournament(tournament_id)

        if not fights:
            return jsonify({
                'success': False,
                'message': 'Нет боев'
            }), 404

        return jsonify({
            'success': True,
            'fights': fights,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка создания сетки: {str(e)}'
        }), 500