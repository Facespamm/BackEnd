from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from new_model.Enums import RoleName
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from utils.security import role_required

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/assign_to_tournament/<int:tournament_id>', methods=['POST'])
@jwt_required()
@role_required(RoleName.ATHLETE.value)
def assign_to_tournament(tournament_id):
    user_id = get_jwt_identity()

    if tournament_id is None:
        return jsonify({
            'success': False,
            'message': 'Вы не выбрали турнир или категорию для регистрации'
        })

    with (TournamentRepository() as tourn_repository,
          AthleteRepository() as athlete_repository):
        tournament = tourn_repository.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({'success': False, 'message': 'Нет такого турнира или категории'}), 400

        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        if athlete_id is None:
            return jsonify({'success': False, 'message': 'Вы не дзюдоист'})

        if tourn_repository.is_registet_on_tournament(tournament_id, athlete_id):
            return jsonify({
                'success': True,
                'message': 'Вы зврегестрированы на этот турнир зарание'
            })

        try:
            has_assigned_athlete = tourn_repository.assign_athletes_tournament(tournament_id, athlete_id,user_id)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка регистрации на турнир:{e}'
            }), 500

        tournament_name = tournament.name
    if has_assigned_athlete:
        return jsonify({
            'success': True,
            'message': f'Вы зарегестрированы на турнир {tournament_name}'
        })


@user_bp.route('/unassign_to_tournament/<int:tournament_id>', methods=['PATCH'])
@jwt_required()
@role_required(RoleName.ATHLETE.value)
def unassign_to_tournament(tournament_id):
    user_id = get_jwt_identity()

    if tournament_id is None:
        return jsonify({
            'success': False,
            'message': 'Вы не выбрали турнир для отмены регистрации'
        })

    with (CategoryRepository() as category_repository,
          TournamentRepository() as tourn_repository,
          AthleteRepository() as athlete_repository):
        tournament = tourn_repository.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({'success': False, 'message': 'Нет такого турнира или категории'}), 404

        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        if athlete_id is None:
            return jsonify({'success': False, 'message': 'Вы не дзюдоист'}), 404
        try:
            has_unassign = tourn_repository.unassign_athlete_to_tournament(tournament_id, athlete_id)
        except Exception as e:
            return jsonify({'success': False,'message':f'Ошибка отмены регистрации:{e}'}),400

    if has_unassign:
        return jsonify({
            'success': True,
            'message': 'Вы отменили регистрацию'
        })

@user_bp.route('/is_registered/<int:tournament_id>', methods=['GET'])
@jwt_required()
@role_required(RoleName.ATHLETE.value)
def is_registered(tournament_id):
    user_id = get_jwt_identity()
    with TournamentRepository() as tourn_repository, AthleteRepository() as athlete_repository:
        athlete_id = athlete_repository.get_athlete_id_by_user(user_id)
        is_registered = tourn_repository.is_registet_on_tournament(tournament_id, athlete_id)
    return jsonify({'is_registered': is_registered})