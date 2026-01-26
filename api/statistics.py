from flask import Blueprint, jsonify
from flasgger import swag_from
from sqlalchemy import func, distinct
from sqlalchemy.orm import joinedload

# Ваши импорты (как указано)
from new_model.head_model.tournament_new import TournamentNew
from new_model.head_model.fight_new import FightNew
from new_model.handbook import new_club
from new_model.head_model import new_athlete
from new_model.head_model import new_user
from new_model.handbook import role_new
from new_model.new_associations import athlete_tournament
from new_model.new_associations import new_user_roles
from new_model.Enums import StatusTournament, FightStatus
from database.db import db

statistics_bp = Blueprint('statistics', __name__, url_prefix='/statistics')



@statistics_bp.route('/live-overview', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Краткая статистика по активным турнирам (LIVE)',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'active_tournaments': {'type': 'integer'},
                            'unique_athletes': {'type': 'integer'},
                            'live_fights': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_live_statistics():
    try:
        active_tournaments_count = (
            db.session.query(func.count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(func.count(FightNew.id))
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
@swag_from({
    'tags': ['Statistics', 'Users'],
    'summary': 'Получить список всех активных пользователей',
    'description': 'Возвращает список активных пользователей с основными данными и их ролями. '
                   'Пароль и служебные поля не возвращаются.',
    'responses': {
        200: {
            'description': 'Список пользователей получен',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'first_name': {'type': 'string'},
                                'last_name': {'type': 'string'},
                                'middle_name': {'type': 'string', 'nullable': True},
                                'email': {'type': 'string', 'nullable': True},
                                'phone': {'type': 'string', 'nullable': True},
                                'is_active': {'type': 'boolean'},
                                'roles': {
                                    'type': 'array',
                                    'items': {'type': 'string'}
                                }
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_all_users():
    """
    Получить список всех активных пользователей с их ролями
    """
    try:
        # Загружаем всех активных пользователей с предзагрузкой ролей
        users = (
            db.session.query(new_user.UserNew)
            .filter(new_user.UserNew.is_active == True)
            .options(joinedload(new_user.UserNew.roles))
            .order_by(new_user.UserNew.last_name, new_user.UserNew.first_name)
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

@statistics_bp.route('/live-detailed', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Расширенная статистика по активным турнирам (LIVE)',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'active_tournaments': {'type': 'integer'},
                            'unique_athletes': {'type': 'integer'},
                            'unique_clubs': {'type': 'integer'},
                            'total_users': {'type': 'integer'},
                            'live_fights': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_live_detailed_statistics():
    try:
        active_tournaments_count = (
            db.session.query(func.count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_clubs_count = (
            db.session.query(func.count(distinct(new_athlete.AthleteNew.club_id)))
            .join(athlete_tournament, new_athlete.AthleteNew.id == athlete_tournament.c.athlete_id)
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(
                TournamentNew.status == StatusTournament.LIVE,
                new_athlete.AthleteNew.club_id.isnot(None)
            )
            .scalar() or 0
        )

        total_users_count = (
            db.session.query(func.count(new_user.UserNew.id))
            .filter(new_user.UserNew.is_active == True)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(func.count(FightNew.id))
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
            'unique_clubs': unique_clubs_count,
            'total_users': total_users_count,
            'live_fights': live_fights_count
        }

        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@statistics_bp.route('/users-by-role', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Статистика пользователей по ролям',
    'description': 'Возвращает общее количество активных пользователей и распределение по ролям',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_active_users': {'type': 'integer'},
                            'users_by_role': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'role_name': {'type': 'string'},
                                        'normalized_name': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            },
                            'users_without_role': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_users_by_role_statistics():
    """
    Получить статистику пользователей по ролям
    """
    try:
        # 1. Общее количество активных пользователей
        total_active_users = (
            db.session.query(func.count(new_user.UserNew.id))
            .filter(new_user.UserNew.is_active == True)
            .scalar() or 0
        )

        # 2. Количество пользователей по каждой роли
        users_by_role = (
            db.session.query(
                role_new.RoleNew.name.label('role_name'),
                role_new.RoleNew.normalized_name.label('normalized_name'),
                func.count(new_user.UserNew.id).label('count')
            )
            .join(new_user_roles, role_new.RoleNew.id == new_user_roles.c.role_id)
            .join(new_user.UserNew, new_user.UserNew.id == new_user_roles.c.user_id)
            .filter(new_user.UserNew.is_active == True)
            .group_by(role_new.RoleNew.id, role_new.RoleNew.name, role_new.RoleNew.normalized_name)
            .order_by(role_new.RoleNew.name)
            .all()
        )

        # 3. Пользователи без ролей (активные)
        users_without_role = (
            db.session.query(func.count(new_user.UserNew.id))
            .outerjoin(new_user_roles, new_user.UserNew.id == new_user_roles.c.user_id)
            .filter(
                new_user.UserNew.is_active == True,
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
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Список всех активных турниров (статус LIVE)',
    'description': 'Возвращает список турниров со статусом LIVE с основной информацией',
    'responses': {
        200: {
            'description': 'Список турниров получен',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'start_date': {'type': 'string'},
                                'end_date': {'type': 'string'},
                                'city': {'type': 'string'},
                                'country': {'type': 'string'},
                                'tatami_count': {'type': 'integer'},
                                'athletes_count': {'type': 'integer'},
                                'live_fights_count': {'type': 'integer'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_active_tournaments():
    """
    Получить список всех турниров со статусом LIVE
    """
    try:
        # Получаем все активные турниры с предзагрузкой связей
        tournaments = (
            db.session.query(TournamentNew)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .options(joinedload(TournamentNew.athletes))
            .all()
        )

        result = []
        for tournament in tournaments:
            # Количество уникальных атлетов на турнире
            athletes_count = (
                db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
                .filter(athlete_tournament.c.tournament_id == tournament.id)
                .scalar() or 0
            )

            # Количество активных боёв на этом турнире
            live_fights_count = (
                db.session.query(func.count(FightNew.id))
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

