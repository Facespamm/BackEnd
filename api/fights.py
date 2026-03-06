from flask import Blueprint, request, jsonify

from database.db import create_session
from new_model.Enums import FightStatus
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.referee_repo import RefereeRepository
from repository.tournament_repo import TournamentRepository
from new_model.Enums import BracketType
from repository.result_repo import ResultRepository

fights_bp = Blueprint('fights', __name__, url_prefix='/api/fights')

@fights_bp.route('/', methods=['GET'])
def get_fights():
    """Получить список схваток"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        status = request.args.get('status')
        tatami = request.args.get('tatami', type=int)

        if not tournament_id:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: tournament_id'
            }), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return jsonify({
                    'success': False,
                    'message': 'Турнир не найден'
                }), 404

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fights_by_search_params(tournament_id, status, tatami)

            result = []
            athlete_repo = AthleteRepository(session)
            for fight in fights:
                fight_data = {
                    'id': fight.id,
                    'tournament_id': fight.tournament_category_id,
                    'tatami': fight.tatami_number,
                    'status': fight.status.value,
                    'round_number': fight.round_number,
                    'fight_number': fight.fight_number,
                    'white_athlete': athlete_repo.get_athlete_by_fight(fight.white_athlete_id, fight.id),
                    'blue_athlete': athlete_repo.get_athlete_by_fight(fight.blue_athlete_id, fight.id),
                }
                result.append(fight_data)

        return jsonify({
            'success': True,
            'fights': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схваток: {str(e)}'
        }), 500

def _build_result_dto(result):
    if not result:
        return None
    return {
        'winner_id':      result.winner_id,
        'victory_type':   result.victory_type.value if result.victory_type else None,
        'fight_duration': result.fight_duration,
    }

def _build_fight_dto(fight, athlete_repo, result_repo=None):
    result = result_repo.get_result_by_fight(fight.id) if result_repo else None
    return {
        'id':            fight.id,
        'round':         fight.round_number,
        'fight_number':  fight.fight_number,
        'status':        fight.status.value,
        'tatami_number': fight.tatami_number,
        'next_fight':    fight.next_fight_id,
        'white_athlete': athlete_repo.get_athlete_by_fight(fight.white_athlete_id, fight.id),
        'blue_athlete':  athlete_repo.get_athlete_by_fight(fight.blue_athlete_id, fight.id),
        'result':        _build_result_dto(result),
    }


@fights_bp.route('/<int:fight_id>', methods=['GET'])
def get_fight(fight_id):
    """Получить информацию о схватке"""
    try:
        if not fight_id:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: fight_id'
            }), 400

        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)

            if not fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            athlete_repo = AthleteRepository(session)
            fight_data = {
                'id': fight.id,
                'tournament_id': fight.tournament_category_id,
                'tatami': fight.tatami_number,
                'status': fight.status.value,
                'round_number': fight.round_number,
                'fight_number': fight.fight_number,
                'white_athlete': athlete_repo.get_athlete_by_fight(fight.white_athlete_id, fight.id),
                'blue_athlete': athlete_repo.get_athlete_by_fight(fight.blue_athlete_id, fight.id),
            }

        return jsonify(fight_data), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схватки: {str(e)}'
        }), 500

@fights_bp.route('/<int:tournament_id>/consolation/finalists', methods=['GET'])
def get_finalists_consolation(tournament_id):
    """Утешительные бои финалистов (группа A и B)"""
    try:
        category_id = request.args.get('category', type=int)
        group = request.args.get('group', '').upper()

        if not category_id:
            return jsonify({'success': False, 'message': 'Не выбрана категория'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)
            if not tournament_category:
                return jsonify({'success': False, 'message': 'Категория турнира не найдена'}), 404

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo   = FightRepository(session)
            athlete_repo = AthleteRepository(session)
            result_repo  = ResultRepository(session)

            groups = {
                'A': BracketType.FINALIST_CONSOLATION_GROUP_A,
                'B': BracketType.FINALIST_CONSOLATION_GROUP_B,
            }
            groups_to_fetch = {group: groups[group]} if group in groups else groups

            result = {}
            for group_name, bracket_type in groups_to_fetch.items():
                fights = fight_repo.get_fights_by_bracket_type(tournament_category_id, bracket_type)
                result[f'group_{group_name}'] = [
                    _build_fight_dto(fight, athlete_repo, result_repo)
                    for fight in fights
                ]

            if not any(result.values()):
                return jsonify({'success': False, 'message': 'Утешительные бои финалистов не найдены'}), 404

        return jsonify({
            'success': True,
            **result,
            'total': sum(len(v) for v in result.values())
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500



@fights_bp.route('/<int:tournament_id>/consolation/semifinalists', methods=['GET'])
def get_semifinalists_consolation(tournament_id):
    """Утешительные бои полуфиналистов — обе группы A и B одним запросом"""
    try:
        category_id = request.args.get('category', type=int)

        if not category_id:
            return jsonify({'success': False, 'message': 'Не выбрана категория'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)
            if not tournament_category:
                return jsonify({'success': False, 'message': 'Категория турнира не найдена'}), 404

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo   = FightRepository(session)
            athlete_repo = AthleteRepository(session)
            result_repo  = ResultRepository(session)

            fights_a = fight_repo.get_fights_by_bracket_type(
                tournament_category_id,
                BracketType.SEMIFINALIST_CONSOLATION_GROUP_A
            )
            fights_b = fight_repo.get_fights_by_bracket_type(
                tournament_category_id,
                BracketType.SEMIFINALIST_CONSOLATION_GROUP_B
            )

            if not fights_a and not fights_b:
                return jsonify({
                    'success': True,
                    'message': 'Утешительные бои пока не созданы',
                    'groups': {'A': [], 'B': []},
                    'total': 0
                }), 200

            fights_dto_a = [_build_fight_dto(f, athlete_repo, result_repo) for f in fights_a]
            fights_dto_b = [_build_fight_dto(f, athlete_repo, result_repo) for f in fights_b]

        return jsonify({
            'success': True,
            'groups': {
                'A': {'fights': fights_dto_a, 'total': len(fights_dto_a)},
                'B': {'fights': fights_dto_b, 'total': len(fights_dto_b)},
            },
            'total': len(fights_dto_a) + len(fights_dto_b)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500


@fights_bp.route('/<int:fight_id>/referees', methods=['GET'])
def get_fight_referees(fight_id):
    """Получить судей, назначенных на схватку"""
    try:
        # ✅ ИСПРАВЛЕНО: было `with FightRepository() as fight_repo`
        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            referee_list = fight_repo.get_fight_referees(fight_id)

        return jsonify({
            'success': True,
            'referees': referee_list
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении судей схватки: {str(e)}'
        }), 500

@fights_bp.route('/<fight_id>/assign_referee', methods=['POST'])
def assign_referee_to_fight(fight_id):
    """Назначить судью на схватку"""
    try:
        data = request.get_json()

        required_fields = ['referee_id', 'role']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Обязательное поле: {missing_fields}'
            }), 400

        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)
            if not fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            referee_repo = RefereeRepository(session)
            referee = referee_repo.get_referee(data['referee_id'])
            if not referee:
                return jsonify({
                    'success': False,
                    'message': 'Судья не найден'
                }), 404

            fight_repo.assign_referee(fight.id, data['referee_id'], data['role'])

        return jsonify({
            'success': True,
            'message': 'Судья успешно назначен на схватку'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при назначении судьи на схватку: {str(e)}'
        }), 500

@fights_bp.route('/<fight_id>/remove_referee', methods=['DELETE'])
def remove_referee_from_fight(fight_id):
    try:
        role = request.args.get('role')

        if not role:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: role'
            }), 400

        with create_session() as session:
            fight_repo = FightRepository(session)
            fight = fight_repo.get_fight_by_id(fight_id)

            if not fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            referee_repo = RefereeRepository(session)
            if not referee_repo.has_assign_referee(role, fight.id):
                return jsonify({
                    'success': False,
                    'message': f'Судья на роль {role} не назначен'
                }), 404

            fight_repo.remove_referee(fight.id, role)

        return jsonify({
            'success': True,
            'message': 'Судья успешно удален с схватки'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении судьи с схватки: {str(e)}'
        }), 500

@fights_bp.route('/<int:fight_id>/set-live', methods=['PATCH'])
def update_fight_status(fight_id):
    try:
        if not fight_id:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: fight_id'
            }), 400

        tatami_number = request.args.get('tatami_number', type=int)

        # ✅ ИСПРАВЛЕНО: было `with FightRepository() as fight_repo`
        with create_session() as session:
            fight_repo = FightRepository(session)
            exiting_fight = fight_repo.get_fight_by_id(fight_id)
            if not exiting_fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            is_taken_tatami = fight_repo.tatami_is_taken(fight_id, tatami_number)

            if is_taken_tatami:
                return jsonify({
                    'message': 'На татами уже идет бой'
                }), 400

            fight_repo.set_live_status(fight_id, tatami_number)

        return jsonify({
            'success': True,
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении статуса схватки: {str(e)}'
        }), 500

@fights_bp.route('/<int:fight_id>/end-fight', methods=['PUT'])
def end_fight(fight_id):
    try:
        if not fight_id:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: fight_id'
            }), 400

        data = request.get_json()
        required_fields = ['start_time', 'end_time', 'winner_athlete_id', 'victory_type']

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Обязательное поле: {missing_fields}'
            }), 400

        # ✅ ИСПРАВЛЕНО: было `with FightRepository() as fight_repo`
        with create_session() as session:
            fight_repo = FightRepository(session)
            exiting_fight = fight_repo.get_fight_by_id(fight_id)
            if not exiting_fight:
                return jsonify({
                    'success': False,
                    'message': 'Схватка не найдена'
                }), 404

            fight_repo.end_fight(fight_id, data)

        return jsonify({
            'success': True,
            'message': 'Схватка успешно завершена'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при завершении схватки: {str(e)}'
        }), 500

@fights_bp.route('/<int:tournament_id>/scheduled/', methods=['GET'])
def fight_bracket(tournament_id):
    try:
        if not tournament_id:
            return jsonify({'success': False, 'message': f'ID турнира не указан'})

        category_id = request.args.get('category')

        if not category_id and type(category_id) != int:
            return jsonify({'success': False, 'message': 'Не выброна категория'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(tournament_id, category_id)
            if not tournament_category:
                return jsonify({
                    'success': False,
                    'message': 'Категория турнира не найдена'
                }), 404

            tournament_category_id = tournament_category.tournament_category_id
            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(tournament_category_id, FightStatus.SCHEDULED)

            fights_dtos = []

            athlete_repo = AthleteRepository(session)
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

            tournament_name = tournament_repo.get_tournament_name_by_tournament_category(tournament_category_id)
            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(category_id)

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