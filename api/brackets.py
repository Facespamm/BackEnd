from flask import request, Blueprint, jsonify

from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.tournament_repo import TournamentRepository
from services.bracket_generator import BracketGenerator
from operator import and_

brackets_bp = Blueprint('brackets', __name__, url_prefix='/api/brackets')

@brackets_bp.route('/<int:tournament_id>', methods=['POST'])
def create_bracket(tournament_id):
    """Создает олимпийскую сетку"""
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

        category_str = request.args.get('category_id')
        if not category_str:
            return jsonify({'success': False, 'message': 'Не выбрана категория'}), 400

        tatami_number = request.args.get('tatami_number')
        if not tatami_number:
            return jsonify({
                'success': False,
                'message': 'Татами не указан'
            }), 400

        try:
            category_id = int(category_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'ID категории должен быть целым числом'}), 400

        tournament_repo = TournamentRepository()
        tournament = tournament_repo.get_tournament_by_id(tournament_id)
        if not tournament:
            return jsonify({'success': False, 'message': 'Турнир не найден'}), 404

        # Исправленный блок
        category = tournament_repo.get_category(tournament_id, category_id)
        if not category:
            return jsonify({'success': False, 'message': 'Категория не найдена в этом турнире'}), 404

        bracket_generator = BracketGenerator(tournament_id)
        generate_fights = bracket_generator.generate_olympic(category_id, tatami_number)

        if not generate_fights:
            return jsonify({
                'success': False,
                'message': 'Не удалось создать бои (возможно, недостаточно спортсменов в категории)'
            }), 400

        return jsonify({
            'success': True,
            'message': 'Сетка успешно создана'
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания сетки: {str(e)}'}), 500

@brackets_bp.route('/<int:tournament_id>/has-consolation', methods=['GET'])
def has_consolation_fights(tournament_id):
    """Проверяет можно ли создать утешительные бои"""
    category_id = request.args.get('category_id')

    if not tournament_id:
        return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

    if not category_id:
        return jsonify({'success': False, 'message': 'ID категории не указан'}), 400

    tournament_repo = TournamentRepository()
    tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)

    if not tournament_category:
        return jsonify({'success': False, 'message': 'Категория турнира не найдена'}), 404

    if not tournament_category.has_consolidation_fights:
        return jsonify({'success': False}), 200

    athlete_repo = AthleteRepository()
    athletes = athlete_repo.get_athletes_by_tournament(tournament_id, category_id)

    total_rounds = BracketGenerator.calculate_rounds(len(athletes))

    fight_repo = FightRepository()
    semi_final_fights = fight_repo.get_semi_final_fights(
        tournament_category.tournament_category_id,
        total_rounds -1
    )

    semi_final_fights_not_none = []
    for fight in semi_final_fights:
        if and_(fight.blue_athlete_id is not None, fight.white_athlete_id is not None):
            semi_final_fights_not_none.append(fight)

    max_semi_final_fights = 2
    if len(semi_final_fights_not_none) < max_semi_final_fights:
        return jsonify({'success': False}), 200

    return jsonify({'success': True}), 200

@brackets_bp.route('/<int:tournament_id>/semifinals-consalation', methods=['POST'])
def generate_semifinals_consolation_fights(tournament_id):
    """Создание утешительных боев от полуфиналистов"""
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        tatami_number = request.args.get('tatami_number')

        if not tatami_number and type(tatami_number) != int:
            return jsonify({'success': False, 'message': 'Не выброн татами'}), 400

        tournament_repo = TournamentRepository()
        tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)

        if not tournament_category:
            return jsonify({'success': False, 'message': 'Категория турнира не найдена'}), 404

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = bracket_generator.generate_olympic_consolation_fight_semifinal(category_id, tatami_number)

        if not generated_fights:
            return jsonify({
                'success': False,
                'message': 'Утешительные бои не созданы'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Утешительные бои успешно созданы'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания утешительных боев: {str(e)}'}), 500

@brackets_bp.route('/<int:tournament_id>/finals-consalation', methods=['POST'])
def generate_consolation_fights_finalist(tournament_id):
    """Создание сетки для утишительных от финалистов """
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': 'ID турнира не указан'}), 400

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        tatami_number = request.args.get('tatami_number')

        if not tatami_number and type(tatami_number) != int:
            return jsonify({'success': False, 'message': 'Не выброн татами'}), 400

        tournament_repo = TournamentRepository()
        tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)

        if not tournament_category:
            return jsonify({'success': False, 'message': 'Категория турнира не найдена'}), 404

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = bracket_generator.generate_olympic_consolation_fight_final(category_id, tatami_number)

        if not generated_fights:
            return jsonify({
                'success': False,
                'message': 'Утешительные бои не созданы'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Утешительные бои успешно созданы'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания утешительных боев: {str(e)}'}), 500

@brackets_bp.route('/<int:tournament_id>/fights/', methods=['GET'])
def fight_bracket(tournament_id):
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': f'ID турнира не указан'})

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        tournament_repo = TournamentRepository()
        tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)
        if not tournament_category:
            return jsonify({
                'success': False,
                'message': 'Категория турнира не найдена'
            }), 404

        tournament_category_id = tournament_category.tournament_category_id
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
                'status_fight': fight.status.value,
                'next_fight': fight.next_fight_id,
            })

        tournament_repo = TournamentRepository()
        tournament_name = tournament_repo.get_tournament_name_by_tournament_category(tournament_category_id)
        category_repo = CategoryRepository()
        category  = category_repo.get_category_by_id(category_id)
        if not fights_dtos:
            return jsonify({
                'success': False,
                'message': 'Нет боев'
            }), 404

        return jsonify({
            'success': True,
            'fights': fights_dtos,
            'tournament_name': tournament_name,
            'category': {
                'id': category.id,
                'name': category.name,
                'weight_range': f'от {category.min_weight} до {category.max_weight}'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка вывода боев: {str(e)}'
        }), 500