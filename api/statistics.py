from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import distinct
from sqlalchemy.sql.functions import count

from new_model.handbook.role_new import RoleNew
from new_model.head_model.new_user import UserNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.head_model.fight_new import FightNew
from new_model.new_associations import new_user_roles, AthleteRegistration, TournamentCategory
from new_model.Enums import StatusTournament, FightStatus
from database.db import create_session

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')

@statistics_bp.route('/live-overview', methods=['GET'])
def get_live_statistics():
    try:
        with create_session() as session:
            active_tournaments_count = (
                session.query(count(TournamentNew.id))
                .filter(TournamentNew.status == StatusTournament.LIVE)
                .scalar() or 0
            )

            unique_athletes_count = (
                 session.query(count(distinct(AthleteRegistration.athlete_id)))
                .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
                .join(TournamentNew, TournamentNew.id == TournamentCategory.tournament_id)
                .filter(TournamentNew.status == StatusTournament.LIVE)
                .scalar() or 0
            )

            live_fights_count = (
                session.query(count(FightNew.id))
                .join(TournamentNew)
                .filter(
                    TournamentNew.status == StatusTournament.LIVE,
                    FightNew.status == FightStatus.LIVE
                )
                .scalar() or 0
            )

        result = {
            'active_tournaments': active_tournaments_count,
            'unique_athletes': unique_athletes_count,
            'live_fights': live_fights_count
        }

        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@statistics_bp.route('/users', methods=['GET'])
def get_all_users():
    """
    Получить список всех активных пользователей с их ролями
    """
    try:
        # Загружаем всех активных пользователей с предзагрузкой ролей
        with create_session() as session:
            users = (
                session.query(UserNew)
                .filter(UserNew.is_active == True)
                .options(joinedload(UserNew.roles))
                .order_by(UserNew.last_name, UserNew.first_name)
                .all()
            )

            result = []
            for user in users:
                # Собираем список названий ролей
                user_roles = [role.name for role in user.roles]

                result.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'middle_name': user.middle_name,
                    'email': user.email,
                    'phone': user.phone,
                    'is_active': user.is_active,
                    'roles': user_roles
                })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении списка пользователей: {str(e)}'
        }), 500

@statistics_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        with create_session() as session:
            user = session.query(UserNew).filter(UserNew.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'message': f'Пользователь с ID {user_id} не найден'}), 404

            username = user.username
            session.delete(user)
            session.commit()  # если упадёт — поймает внешний except

        return jsonify({'success': True, 'message': f'Пользователь {username} успешно удалён'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при удалении пользователя: {str(e)}'}), 500

# ────────────────────────────────────────────────────────────────
# ОБНОВЛЕНИЕ данных пользователя по ID
# ────────────────────────────────────────────────────────────────
@statistics_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({'success': False, 'message': 'Не переданы данные для обновления'}), 400

        with create_session() as session:
            user = session.query(UserNew).filter(UserNew.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'message': f'Пользователь с ID {user_id} не найден'}), 404

            if 'username' in data:
                user.username = data['username']
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'middle_name' in data:
                user.middle_name = data['middle_name']
            if 'email' in data:
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
            if 'is_active' in data:
                user.is_active = data['is_active']

            try:
                session.commit()
            except:
                session.rollback()
                return jsonify({'success': False, 'message': 'Ошибка при сохранении'}), 500

            # ← собираем ответ пока сессия ещё открыта
            user_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active
            }

        return jsonify({'success': True, 'message': 'Пользователь успешно обновлён', 'user': user_data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при обновлении пользователя: {str(e)}'}), 500
@statistics_bp.route('/users-by-role', methods=['GET'])
def get_users_by_role_statistics():
    """
    Получить статистику пользователей по ролям
    """
    try:
        with create_session() as session:
            # 1. Общее количество активных пользователей
            total_active_users = (
                session.query(count(UserNew.id))
                .filter(UserNew.is_active == True)
                .scalar() or 0
            )

            # 2. Количество пользователей по каждой роли
            users_by_role = (
                session.query(
                    RoleNew.name.label('role_name'),
                    RoleNew.normalized_name.label('normalized_name'),
                    count(UserNew.id).label('count')
                )
                .join(new_user_roles, RoleNew.id == new_user_roles.c.role_id)
                .join(UserNew, UserNew.id == new_user_roles.c.user_id)
                .filter(UserNew.is_active == True)
                .group_by(RoleNew.id, RoleNew.name, RoleNew.normalized_name)
                .order_by(RoleNew.name)
                .all()
            )

            # 3. Пользователи без ролей (активные)
            users_without_role = (
                session.query(count(UserNew.id))
                .outerjoin(new_user_roles, UserNew.id == new_user_roles.c.user_id)
                .filter(
                    UserNew.is_active == True,
                    new_user_roles.c.user_id.is_(None)
                )
                .scalar() or 0
            )

        # Формируем список ролей
        role_list = [
            {
                'role_name': role.role_name,
                'normalized_name': role.normalized_name,
                'count': role.count
            }
            for role in users_by_role
        ]

        result = {
            'total_active_users': total_active_users,
            'users_by_role': role_list,
            'users_without_role': users_without_role
        }

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении статистики пользователей: {str(e)}'
        }), 500

@statistics_bp.route('/active-tournaments', methods=['GET'])
def get_active_tournaments():
    """
    Получить список всех турниров со статусом LIVE
    """
    try:
        with create_session() as session:
            #Получаем все активные турниры с предзагрузкой связей
            tournaments = (
                session.query(TournamentNew)
                .filter(TournamentNew.status == StatusTournament.LIVE)
                .options(joinedload(TournamentNew.athletes))
                .all()
            )

            result = []
            for tournament in tournaments:
                # Количество уникальных атлетов на турнире
                athletes_count = (
                    session.query(count(distinct(AthleteRegistration.athlete_id)))
                    .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
                    .filter(TournamentCategory.tournament_id == tournament.id)
                    .scalar() or 0
                )

                # Количество активных боёв на этом турнире
                live_fights_count = (
                    session.query(count(FightNew.id))
                    .filter(
                        FightNew.tournament_id == tournament.id,
                        FightNew.status == FightStatus.LIVE
                    )
                    .scalar() or 0
                )

            result.append({
                'id': tournament.id,
                'name': tournament.name,
                'start_date': tournament.start_date.isoformat() if tournament.start_date else None,
                'end_date': tournament.end_date.isoformat() if tournament.end_date else None,
                'city': tournament.city,
                'country': tournament.country,
                'tatami_count': tournament.tatami_count,
                'athletes_count': athletes_count,
                'live_fights_count': live_fights_count
            })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении списка турниров: {str(e)}'
        }), 500

