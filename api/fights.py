from flask import Blueprint, request, jsonify

from repository.athlete_repo import AthleteRepository
from repository.figth_repo import FightRepository
from repository.referee_repo import RefereeRepository
from repository.tournament_repo import TournamentRepository

fights_bp = Blueprint('fights', __name__, url_prefix='/api/fights')
fight_repo = FightRepository()

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

        tournament_repo = TournamentRepository()
        tournament = tournament_repo.get_tournament_by_id(tournament_id)
        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        fights = fight_repo.get_fights_by_search_params(tournament_id, status, tatami)

        result = []
        athlete_repo = AthleteRepository()
        for fight in fights:
            fight_data = {
                'id': fight.id,
                'tournament_id': fight.tournament_category_id,
                'tatami': fight.tatami_number,
                'status': fight.status,
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

@fights_bp.route('/<int:fight_id>', methods=['GET'])
def get_fight(fight_id):
    """Получить информацию о схватке"""
    try:
        if not fight_id:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: fight_id'
            }), 400

        fight = fight_repo.get_fight_by_id(fight_id)

        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        athlete_repo = AthleteRepository()
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

@fights_bp.route('/<int:fight_id>/referees', methods=['GET'])
def get_fight_referees(fight_id):
    """Получить судей, назначенных на схватку"""
    try:
        fight = fight_repo.get_fight_by_id(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        referees = fight_repo.get_fight_referees(fight_id)
        referee_list = referees


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

        fight = fight_repo.get_fight_by_id(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        referee_repo = RefereeRepository()
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
        role =request.args.get('role')

        if not role:
            return jsonify({
                'success': False,
                'message': 'Обязательный параметр: role'
            }), 400

        fight = fight_repo.get_fight_by_id(fight_id)

        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        referee_repo = RefereeRepository()
        if not referee_repo.has_assign_referee(role , fight.id):
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

        exiting_fight = fight_repo.get_fight_by_id(fight_id)
        if not exiting_fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

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